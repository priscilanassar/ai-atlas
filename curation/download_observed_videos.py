"""Download only public CDN files already observed in the rendered source page."""
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from urllib.request import Request, urlopen

BASE=Path(__file__).resolve().parent.parent
rows=json.loads((BASE/'curation/saved-oct26-video-sample.json').read_text(encoding='utf-8'))
for row in rows:
    # Resource inventories can contain just a DASH index-range request. Request
    # the same observed CDN file in full, preserving all signature parameters.
    parsed=urlparse(row['url'])
    url=urlunparse(parsed._replace(query=urlencode([(k,v) for k,v in parse_qsl(parsed.query)
                                                   if k not in ('bytestart','byteend')])))
    host=urlparse(url).hostname or ''
    if not host.endswith(('.fbcdn.net','.cdninstagram.com')): raise ValueError('Unexpected media host')
    target=BASE/'media/projects/source-videos'/row['code']/(row['id']+'.mp4')
    target.parent.mkdir(parents=True,exist_ok=True)
    try:
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as response:
            if not (urlparse(response.geturl()).hostname or '').endswith(('.fbcdn.net','.cdninstagram.com')):
                raise ValueError('Unexpected redirect')
            data=response.read(32*1024*1024+1)
            if len(data)>32*1024*1024 or b'ftyp' not in data[:64]: raise ValueError('Not a supported MP4')
            target.write_bytes(data)
        row['file']=str(target.relative_to(BASE/'media')).replace('\\','/')
        row['bytes']=len(data)
        print(row['id'],len(data),'bytes')
    except (OSError,ValueError) as error:
        row['error']=str(error)
        print(row['id'],str(error))
(BASE/'curation/saved-oct26-video-sample-download.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
