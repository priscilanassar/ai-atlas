"""Download official Google Fonts subsets and their OFL notices."""
import re
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parent.parent/'static'/'fonts'
root.mkdir(exist_ok=True)
families = ['Allura','Great Vibes','Inter:wght@400','Manrope:wght@400','Space Grotesk:wght@500']
query = urlencode([('family',family) for family in families]+[('text','ATLAS'),('display','swap')])
headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
with urlopen(Request('https://fonts.googleapis.com/css2?'+query,headers=headers),timeout=25) as response:
    css=response.read().decode()
output=[]
for block in re.findall(r'@font-face\s*\{(.*?)\}',css,re.S):
    family=re.search(r"font-family:\s*['\"]([^'\"]+)",block)[1]
    url=re.search(r'url\(([^)]+)\)',block)[1]
    if urlparse(url).hostname!='fonts.gstatic.com':raise ValueError('Unexpected font host')
    with urlopen(Request(url,headers=headers),timeout=25) as response:data=response.read()
    if data[:4]==b'wOF2':extension,kind='woff2','woff2'
    elif data[:4]==b'wOFF':extension,kind='woff','woff'
    elif data[:4] in (b'\x00\x01\x00\x00',b'OTTO'):extension,kind='ttf','truetype'
    else:raise ValueError('Invalid font file')
    name=family.replace(' ','')+'.'+extension
    (root/name).write_bytes(data)
    weight=re.search(r'font-weight:\s*([^;]+)',block)[1]
    output.append(f"@font-face {{ font-family: 'Atlas {family}'; font-style: normal; font-weight: {weight}; font-display: swap; src: url('./{name}') format('{kind}'); }}")
    license_dir=family.replace(' ','').lower()
    with urlopen(f'https://raw.githubusercontent.com/google/fonts/main/ofl/{license_dir}/OFL.txt',timeout=25) as response:
        (root/(family.replace(' ','')+'-OFL.txt')).write_bytes(response.read())
    print(f'{family}: {len(data)} bytes')
(root/'atlas-fonts.css').write_text('\n'.join(output)+'\n',encoding='utf-8')
