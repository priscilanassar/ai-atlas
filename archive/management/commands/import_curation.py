import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import transaction

from archive.models import CurationSubmission


class Command(BaseCommand):
    help = 'Import reviewed public Instagram metadata into the curation inbox without publishing projects.'

    def add_arguments(self, parser):
        parser.add_argument('path', type=Path)

    def handle(self, path, **options):
        try:
            rows = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError) as error:
            raise CommandError(str(error)) from error
        if not isinstance(rows, list):
            raise CommandError('Expected a JSON list.')
        prepared = []
        for index, row in enumerate(rows, 1):
            if not isinstance(row, dict):
                raise CommandError(f'Row {index}: expected an object.')
            url = row.get('source_url', '')
            parsed = urlparse(url)
            match = re.fullmatch(r'/(?:[\w.]+/)?(p|reel)/([\w-]+)/?', parsed.path)
            if parsed.scheme != 'https' or parsed.netloc not in ('www.instagram.com', 'instagram.com') or not match:
                raise CommandError(f'Row {index}: invalid Instagram URL.')
            preview = row.get('preview_url', '')
            try:
                if preview:
                    URLValidator(schemes=['https'])(preview)
                published = date.fromisoformat(row['published_on']) if row.get('published_on') else None
            except (ValidationError, ValueError, TypeError) as error:
                raise CommandError(f'Row {index}: invalid date or preview URL.') from error
            prepared.append((f'instagram:{match[2]}', {
                'source_url': url, 'media_type': 'reel' if match[1] == 'reel' else 'post',
                'publisher': row.get('publisher', '')[:100], 'published_on': published,
                'caption_excerpt': ' '.join(row.get('caption_excerpt', '').split()[:25]),
                'suggested_title': row.get('title', '')[:200], 'preview_url': preview,
                'artist': row.get('artist_credit', '')[:200], 'tools': row.get('tools', '')[:300],
                'notes': row.get('notes', ''),
            }))
        created_count = 0
        with transaction.atomic():
            for key, defaults in prepared:
                _, created = CurationSubmission.objects.get_or_create(source_key=key, defaults=defaults)
                created_count += int(created)
        self.stdout.write(self.style.SUCCESS(
            f'{created_count} added to the inbox; {len(prepared) - created_count} already existed. No projects published.'))
