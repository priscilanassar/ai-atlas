"""Cache validated covers and build a visual review sheet before publishing."""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / '.venv/Lib/site-packages'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from archive.management.commands.import_instagram_scrape import cache_image
from PIL import Image, ImageDraw, ImageFont, ImageOps

rows = json.loads((BASE/'curation/saved-oct26-selected.json').read_text(encoding='utf-8'))
def cache(row):
    row['cover_file'] = cache_image(row['cover'], row['code'], 'cover')
    if not row['cover_file']:
        raise RuntimeError(f'Missing cover: {row["code"]}')
    return row
with ThreadPoolExecutor(max_workers=4) as pool:
    rows = list(pool.map(cache, rows))
(BASE/'curation/saved-oct26-selected.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 14)
cols, cell_w, cell_h = 6, 205, 250
sheet = Image.new('RGB',(cols*cell_w,((len(rows)+cols-1)//cols)*cell_h),'#f2f2ef')
draw=ImageDraw.Draw(sheet)
for index,row in enumerate(rows):
    x,y=index%cols*cell_w,index//cols*cell_h
    with Image.open(BASE/'media'/row['cover_file']) as source:
        image=ImageOps.contain(source.convert('RGB'),(195,195))
        sheet.paste(image,(x+(195-image.width)//2,y+(195-image.height)//2))
    draw.text((x+4,y+199),f'{index+1:02d} @{row["username"][:20]}',font=font,fill='#111')
    draw.text((x+4,y+219),row['code'],font=font,fill='#111')
output=BASE.parent/'outputs/01a17412-curation/saved-oct26-contact-sheet.jpg'
output.parent.mkdir(parents=True,exist_ok=True)
sheet.save(output,quality=90)
print(f'{len(rows)} covers cached. Review sheet: {output}')
