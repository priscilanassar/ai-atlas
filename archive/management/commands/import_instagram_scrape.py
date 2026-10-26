import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime

from archive.models import Project, CurationSubmission


def media_url(value):
    if not isinstance(value, str):
        return ''
    parsed = urlparse(value)
    host = parsed.hostname or ''
    if parsed.scheme != 'https' or parsed.port or not host.endswith(('.cdninstagram.com', '.fbcdn.net')):
        return ''
    return value


def cache_image(url, shortcode, name):
    relative = Path('projects') / 'instagram' / shortcode / f'{name}.jpg'
    target = Path(settings.MEDIA_ROOT) / relative
    if target.is_file():
        return relative.as_posix()
    try:
        with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=18) as response:
            if not media_url(response.geturl()) or not response.headers.get_content_type().startswith('image/'):
                return ''
            data = response.read(16 * 1024 * 1024 + 1)
        if len(data) > 16 * 1024 * 1024 or not data.startswith((b'\xff\xd8\xff', b'\x89PNG', b'RIFF')):
            return ''
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return relative.as_posix()
    except (OSError, ValueError):
        return ''


class Command(BaseCommand):
    help = 'Publish an Instagram scraper JSON batch with deduplication by shortcode. Comments and account statistics are ignored.'

    def add_arguments(self, parser):
        parser.add_argument('path', type=Path)
        parser.add_argument('--curation', type=Path)
        parser.add_argument('--download-images', action='store_true')

    def handle(self, path, curation=None, download_images=False, **options):
        try:
            records = json.loads(path.read_text(encoding='utf-8'))
            curated = json.loads(curation.read_text(encoding='utf-8')) if curation else []
        except (OSError, ValueError) as error:
            raise CommandError(str(error)) from error
        if not isinstance(records, list):
            raise CommandError('Expected a list of scraper records.')
        curated_by_code = {urlparse(row['url']).path.rstrip('/').split('/')[-1]: row for row in curated}
        prepared = []
        for row in records:
            url = row.get('url', '')
            parsed = urlparse(url)
            match = re.fullmatch(r'/(?:[\w.]+/)?(p|reel)/([\w-]+)/?', parsed.path)
            if parsed.scheme != 'https' or parsed.netloc not in ('www.instagram.com', 'instagram.com') or not match:
                raise CommandError('Invalid Instagram source URL.')
            shortcode = match[2]
            username = row.get('user_posted', '')
            if not isinstance(username, str) or not re.fullmatch(r'[\w.]{1,100}', username):
                raise CommandError(f'{shortcode}: missing or invalid publishing account.')
            cover = media_url(row.get('thumbnail'))
            if not cover:
                raise CommandError(f'{shortcode}: missing supported cover URL.')
            caption = row.get('description') or ''
            metadata = curated_by_code.get(shortcode, {})
            title = metadata.get('summary') or caption.split('\n')[0].strip()
            if not re.search(r'[^\W\d_]{3}', title, re.UNICODE):
                title = f'Visual study by @{username}'
            published = parse_datetime(row.get('date_posted', ''))
            if not published:
                raise CommandError(f'{shortcode}: missing publication date.')
            assets = []
            for item in row.get('post_content') or []:
                source = media_url(item.get('url'))
                if source:
                    assets.append({'kind': 'video' if item.get('type', '').lower() == 'video' else 'image', 'url': source})
            style = metadata.get('style', '').lower()
            category = metadata.get('category')
            if category not in dict(Project.CATEGORY_CHOICES):
                category = 'FASHION' if any(value in style for value in ('moda', 'beleza', 'joalheria')) else 'DESIGN' if 'branding' in style else 'FILM' if match[1] == 'reel' else 'AI'
            disclosure = {'Não confirmado': 'AI use not specified in the source caption',
                          'Declarado na legenda': 'AI use declared by the publisher',
                          'Ferramenta indicada': 'Generative tools identified in the source caption'}.get(metadata.get('ai'), '')
            prepared.append({'code': shortcode, 'cover': cover, 'assets': assets, 'defaults': {
                'title': title[:200], 'title_is_editorial': bool(metadata.get('summary')) or title.startswith('Visual study'),
                'artist': metadata.get('artist_credit') or ('Eliza Sofia (@directedbyeliza)' if shortcode == 'DWOs1UYDLRi' else 'Beatrice von Winterfeldt' if username == 'desyre.ai' else f'@{username}'),
                'instagram_username': username, 'instagram_caption': row.get('original_caption') or caption, 'published_at': published,
                'source_url': url,
                'description': metadata.get('description') or (metadata.get('summary', '') + ('\n\n' if metadata.get('summary') else '') + caption),
                'tools': metadata.get('tools', ''), 'year': published.year, 'category': category,
                'ai_disclosure': metadata.get('ai_disclosure') or disclosure,
            }})

        def prepare_media(item):
            cover_file = cache_image(item['cover'], item['code'], 'cover') if download_images else ''
            item['cover_file'] = cover_file
            for index, asset in enumerate(item['assets']):
                asset['original_url'] = asset['url']
                asset['is_cover'] = asset['kind'] == 'image' and asset['url'] == item['cover']
                if asset['kind'] == 'image' and download_images:
                    cached = cache_image(asset['url'], item['code'], f'image-{index + 1}')
                    if cached:
                        asset['url'] = settings.MEDIA_URL + cached
            return item

        with ThreadPoolExecutor(max_workers=6) as executor:
            prepared = list(executor.map(prepare_media, prepared))
        created = updated = cached = 0
        with transaction.atomic():
            for item in prepared:
                project = Project.objects.filter(instagram_shortcode=item['code']).first()
                if project is None:
                    existing = CurationSubmission.objects.filter(source_key=f'instagram:{item["code"]}', project__isnull=False).first()
                    project = existing.project if existing else None
                if project is None:
                    project = Project.objects.create(instagram_shortcode=item['code'], **item['defaults'])
                    created += 1
                else:
                    project.instagram_shortcode = item['code']
                    # Preserve curated title, description and artist on repeated imports.
                    project.instagram_username = item['defaults']['instagram_username']
                    project.instagram_caption = item['defaults']['instagram_caption']
                    project.published_at = item['defaults']['published_at']
                    updated += 1
                # Local media avoids relying on temporary Instagram cover URLs.
                if item['cover_file']:
                    project.cover_file = item['cover_file']
                    cached += 1
                project.image = item['cover']
                project.media_items = item['assets']
                project.save()
                CurationSubmission.objects.filter(source_key=f'instagram:{item["code"]}').update(project=project, status='published')
        self.stdout.write(self.style.SUCCESS(f'{created} projects added; {updated} updated; {cached}/{len(prepared)} covers stored locally.'))
