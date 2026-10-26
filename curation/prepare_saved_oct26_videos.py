"""Cache the first clip of each reviewed post from observed public media URLs."""
import base64
import concurrent.futures
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / '.tools/python'))
sys.path.insert(0, str(BASE / '.venv/Lib/site-packages'))
import imageio_ffmpeg
from PIL import Image, ImageDraw
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUTPUT = BASE.parent / 'outputs/01a17412-curation'

def encoding(asset):
    value = parse_qs(urlparse(asset['url']).query).get('efg', [''])[0]
    return json.loads(base64.urlsafe_b64decode(value + '=' * (-len(value) % 4)))

def download(asset, folder):
    parsed = urlparse(asset['url'])
    url = urlunparse(parsed._replace(query=urlencode([
        (k, v) for k, v in parse_qsl(parsed.query) if k not in ('bytestart', 'byteend')])))
    if not (parsed.hostname or '').endswith(('.fbcdn.net', '.cdninstagram.com')):
        raise ValueError('Unexpected media host')
    target = folder / (asset['id'] + '.mp4')
    if not target.exists():
        with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=35) as response:
            if not (urlparse(response.geturl()).hostname or '').endswith(('.fbcdn.net', '.cdninstagram.com')):
                raise ValueError('Unexpected redirect')
            data = response.read(80 * 1024 * 1024 + 1)
            if len(data) > 80 * 1024 * 1024 or b'ftyp' not in data[:64]:
                raise ValueError('Not a supported MP4')
            target.write_bytes(data)
    return target, url

def run(args):
    return subprocess.run([FFMPEG, '-y', '-v', 'error', *map(str, args)],
        capture_output=True, text=True, timeout=150, check=True,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

def prepare(row):
    code = row['code']
    folder = BASE / 'media/projects/videos/instagram' / code
    folder.mkdir(parents=True, exist_ok=True)
    assets = [(asset, encoding(asset)) for asset in row['videos']]
    first_id = assets[0][1]['xpv_asset_id']
    group = [(a, e) for a, e in assets if e['xpv_asset_id'] == first_id]
    candidates = [(a, e) for a, e in group if 'audio' not in e['vencode_tag']]
    # A moderate observed rendition retains detail while keeping downloads small.
    candidate, meta = min(candidates, key=lambda pair: abs(pair[1].get('bitrate', 0) - 500000))
    source, url = download(candidate, folder)
    probe = subprocess.run([FFMPEG, '-i', str(source)], capture_output=True, text=True,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).stderr
    if 'Video:' not in probe:
        raise ValueError(f'{code}: selected asset is not a video')
    audio = next((a for a, e in group if 'audio' in e['vencode_tag']), None)
    audio_source = download(audio, folder)[0] if audio else None
    preview, playback, frame = folder/'preview.mp4', folder/'playback.mp4', folder/'review.jpg'
    if not preview.exists():
        run(['-i', source, '-t', '12', '-vf',
             'scale=320:320:force_original_aspect_ratio=decrease:force_divisible_by=2,fps=15',
             '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '32',
             '-pix_fmt', 'yuv420p', '-movflags', '+faststart', preview])
    if not playback.exists():
        inputs = ['-i', source]
        if audio_source:
            inputs += ['-i', audio_source, '-map', '0:v:0', '-map', '1:a:0', '-shortest']
        run(inputs + ['-vf', 'scale=480:480:force_original_aspect_ratio=decrease:force_divisible_by=2,fps=24',
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart', playback])
    run(['-ss', str(min(3, meta.get('duration_s', 5)/2)), '-i', playback, '-frames:v', '1', frame])
    result = dict(code=code, original_url=url, source_page=row['page'], asset_id=first_id,
        duration=meta.get('duration_s'), audio=bool(audio_source or 'Audio:' in probe),
        source_file=source.relative_to(BASE/'media').as_posix(),
        preview_file=preview.relative_to(BASE/'media').as_posix(),
        playback_file=playback.relative_to(BASE/'media').as_posix(),
        preview_bytes=preview.stat().st_size, playback_bytes=playback.stat().st_size,
        playback_sha256=hashlib.sha256(playback.read_bytes()).hexdigest())
    print(code, 'ready', result['playback_bytes'], 'bytes', flush=True)
    return result

def main():
    inventory = json.loads((BASE/'curation/saved-oct26-video-inventory.json').read_text(encoding='utf-8'))
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(prepare, row): row['code'] for row in inventory}
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as error:
                results.append(dict(code=futures[future], error=str(error)))
                print(futures[future], 'FAILED', str(error), flush=True)
            (BASE/'curation/saved-oct26-video-prepared.json').write_text(
                json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    sheet = Image.new('RGB', (1200, 6*245), '#eeeeee')
    draw = ImageDraw.Draw(sheet)
    for index, row in enumerate(inventory):
        x, y = (index%4)*300, (index//4)*245
        path = BASE/'media/projects/videos/instagram'/row['code']/'review.jpg'
        if path.exists():
            with Image.open(path) as image:
                image.thumbnail((290, 210))
                sheet.paste(image, (x+(300-image.width)//2, y))
        draw.text((x+10, y+218), row['code'], fill='#111111')
    sheet.save(OUTPUT/'saved-oct26-video-review.jpg', quality=90)
    print(f'{sum("error" not in r for r in results)}/{len(results)} videos prepared')

if __name__ == '__main__':
    main()
