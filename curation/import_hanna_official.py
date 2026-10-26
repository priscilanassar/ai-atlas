"""Import six reviewed AI projects from Hanna Inaiáh's public portfolio."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / '.venv/Lib/site-packages'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from archive.models import Project

copy = [
 ('Lollapalooza Brasil — Espresso', 'An original festival poster by Hanna Inaiáh, inspired by Sabrina Carpenter’s Espresso. An oversized pink coffee machine, botanical motifs and tactile lettering bring music and visual storytelling together. The artist includes this project in her AI portfolio.'),
 ('Latin American Fashion Awards — Second Edition', 'Hanna Inaiáh contributes artwork to the second Latin American Fashion Awards, combining tropical references, texture and a celebration of Latin creative identity. The project is listed in the artist’s AI portfolio.'),
 ('Urban Flora — Animale', 'A project for Animale in which Hanna Inaiáh uses artificial intelligence to merge urban architecture and vegetation. The compositions explore the relationship between built structures and organic life.'),
 ('Artpoint — Beaugrenelle Exhibition', 'AI-generated portraits by Hanna Inaiáh exhibited across seven digital displays at Beaugrenelle in Paris. Fashion imagery, botanical textures and Brazilian cultural references come together in the series.'),
 ('Tropical Christmas — Fairmont Rio', 'A series of AI-generated artworks that reimagines Christmas through the colours and natural forms of Rio de Janeiro. The project was first exhibited at Fairmont Rio.'),
 ('Mooui × Hanna Inaiáh', 'A collaboration combining AI-generated art, surreal landscapes, cosmic motifs and vibrant prints. Hanna Inaiáh explores childhood imagination through textile and surface design for Mooui.'),
]
rows = json.loads((BASE / 'curation/hanna-official-research.json').read_text(encoding='utf-8'))
report = []
for row, (title, description) in zip(rows, copy):
    slug = row['url'].rstrip('/').split('/')[-1]
    assets = []
    seen = set()
    for index, image in enumerate(row['images']):
        url = image['url']
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname != 'cdn.shopify.com' or not parsed.path.startswith('/s/files/1/0805/5013/4034/files/'):
            continue
        if parsed.path in seen:
            continue
        seen.add(parsed.path)
        relative = Path('projects/portfolio/hannainaiah') / slug / (str(index) + Path(parsed.path).suffix)
        target = Path(settings.MEDIA_ROOT) / relative
        if not target.exists():
            with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25) as response:
                if urlparse(response.geturl()).hostname != 'cdn.shopify.com' or not response.headers.get_content_type().startswith('image/'):
                    raise ValueError('Unexpected image response')
                data = response.read(16 * 1024 * 1024 + 1)
            if len(data) > 16 * 1024 * 1024:
                raise ValueError('Image too large')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        assets.append({'kind': 'image', 'url': settings.MEDIA_URL + relative.as_posix(), 'original_url': url, 'is_cover': not assets})
    if not assets:
        raise ValueError(f'No image for {slug}')
    date_line = row['text'].splitlines()[1]
    published = datetime.strptime(date_line, '%B %d, %Y').replace(tzinfo=timezone.utc)
    project, created = Project.objects.get_or_create(source_url=row['url'].replace('/pt/blogs/', '/blogs/'), defaults={
        'title': title, 'artist': 'Hanna Inaiáh', 'category': 'AI', 'description': description,
        'instagram_username': 'hannainaiah', 'year': published.year, 'published_at': published,
        'image': row['images'][0]['url'], 'cover_file': assets[0]['url'].removeprefix(settings.MEDIA_URL),
        'media_items': assets, 'title_is_editorial': True,
        'ai_disclosure': 'AI use documented in the artist’s official AI portfolio',
    })
    report.append({'id': project.pk, 'title': title, 'created': created, 'source': project.source_url, 'images': len(assets)})
(BASE / 'curation/hanna-official-import-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=True))
