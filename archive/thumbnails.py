"""Small gallery covers. Originals are retained for the project detail page."""
import hashlib
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.base import ContentFile


def prepare_thumbnail(project, force=False):
    if not project.cover_file or (not force and project.thumbnail_file and project.thumbnail_source == project.cover_file.name):
        return False
    with project.cover_file.open('rb') as source, Image.open(source) as original:
        image = ImageOps.exif_transpose(original)
        image.thumbnail((320, 320), Image.Resampling.LANCZOS)
        image = image.convert('RGBA' if 'A' in image.getbands() else 'RGB')
        buffer = BytesIO()
        image.save(buffer, format='WEBP', quality=72, method=4)
    payload = buffer.getvalue()
    name = f'projects/thumbnails/{hashlib.sha256(payload).hexdigest()[:24]}.webp'
    storage = project.thumbnail_file.storage
    if not storage.exists(name):
        name = storage.save(name, ContentFile(payload))
    project.thumbnail_file.name = name
    project.thumbnail_source = project.cover_file.name
    return True
