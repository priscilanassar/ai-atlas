"""Cache public video sources and build lightweight silent previews."""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from archive.models import Project


def allowed_video_url(url):
    p = urlparse(url)
    return p.scheme == 'https' and not p.port and (p.hostname or '').endswith(('.cdninstagram.com', '.fbcdn.net'))


class Command(BaseCommand):
    help = 'Cache the first available video in each project and create a 320px / 15fps / 12-second preview.'

    def add_arguments(self, parser):
        parser.add_argument('--project', type=int)

    def handle(self, project=None, **options):
        sys.path.insert(0, str(settings.BASE_DIR / '.tools/python'))
        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError as error:
            raise CommandError('Install imageio-ffmpeg or configure IMAGEIO_FFMPEG_EXE.') from error
        projects = Project.objects.all()
        if project:
            projects = projects.filter(pk=project)
        jobs = [(p.pk, p.media_items) for p in projects if any(m.get('kind') == 'video' for m in p.media_items)]

        def prepare(job):
            pk, items = job
            for index, item in enumerate(items):
                if item.get('kind') != 'video':
                    continue
                directory = Path(settings.MEDIA_ROOT) / 'projects/videos' / str(pk)
                source = directory / f'{index}-source.mp4'
                preview = directory / f'{index}-preview.mp4'
                playback = directory / f'{index}-playback.mp4'
                try:
                    if not source.exists():
                        url = item.get('original_url') or item.get('url', '')
                        if not allowed_video_url(url):
                            continue
                        directory.mkdir(parents=True, exist_ok=True)
                        part = source.with_suffix('.part')
                        try:
                            with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25) as response, part.open('wb') as target:
                                if not allowed_video_url(response.geturl()) or response.headers.get_content_type() not in ('video/mp4', 'application/octet-stream'):
                                    raise ValueError('Unsupported video response')
                                size = 0
                                while data := response.read(1024 * 1024):
                                    size += len(data)
                                    if size > 80 * 1024 * 1024:
                                        raise ValueError('Video larger than 80 MB')
                                    target.write(data)
                            with part.open('rb') as check:
                                if b'ftyp' not in check.read(40):
                                    raise ValueError('Invalid MP4 file')
                            part.replace(source)
                        finally:
                            part.unlink(missing_ok=True)
                    if not preview.exists():
                        output = preview.with_name(preview.stem + '.tmp.mp4')
                        try:
                            subprocess.run([ffmpeg, '-y', '-v', 'error', '-i', str(source), '-t', '12', '-vf',
                                'scale=320:320:force_original_aspect_ratio=decrease:force_divisible_by=2,fps=15',
                                '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '32', '-pix_fmt', 'yuv420p',
                                '-movflags', '+faststart', str(output)], check=True, timeout=90, capture_output=True,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                            output.replace(preview)
                        finally:
                            output.unlink(missing_ok=True)
                    if not playback.exists():
                        output = playback.with_name(playback.stem + '.tmp.mp4')
                        try:
                            subprocess.run([ffmpeg, '-y', '-v', 'error', '-i', str(source), '-vf',
                                'scale=480:480:force_original_aspect_ratio=decrease:force_divisible_by=2,fps=24',
                                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', '-pix_fmt', 'yuv420p',
                                '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart', str(output)],
                                check=True, timeout=120, capture_output=True,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                            output.replace(playback)
                        finally:
                            output.unlink(missing_ok=True)
                    prefix = settings.MEDIA_URL + f'projects/videos/{pk}/'
                    item.setdefault('original_url', item['url'])
                    item['url'] = prefix + source.name
                    item['preview_url'] = prefix + preview.name
                    item['playback_url'] = prefix + playback.name
                    item['preview_width'] = 320
                    return pk, items, None
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    last_error = str(error)
            return pk, None, locals().get('last_error', 'No accessible video source')

        prepared = 0
        with ThreadPoolExecutor(max_workers=3) as pool:
            for pk, items, error in pool.map(prepare, jobs):
                if items:
                    Project.objects.filter(pk=pk).update(media_items=items)
                    prepared += 1
                else:
                    self.stderr.write(f'Project {pk}: {error}')
        self.stdout.write(self.style.SUCCESS(f'{prepared}/{len(jobs)} projects have local lightweight video previews.'))
