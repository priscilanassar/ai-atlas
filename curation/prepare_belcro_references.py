"""Select BELCRO posts with explicit, project-level AI disclosure."""
import json
import re
from datetime import datetime
from pathlib import Path

root = Path(__file__).resolve().parent
research = json.loads((root/'belcro-research.json').read_text(encoding='utf-8'))
selected = {
    'DZdO5sbEXXD': (
        'Web AI Explorations — Pull&Bear', 'DESIGN',
        'AI explorations created by BELCRO for Pull&Bear’s web presence. The original publication explicitly describes the project as web AI explorations and thanks @velasco.moreno.'),
    'DXw-kwoF4X5': (
        'AI Generations — Turismo de Tenerife', 'FILM',
        'BELCRO’s AI-generated contributions to a Turismo de Tenerife production. Directed by Joaquín Luna, with cinematography by Joel Ges Marien, the project credits BELCRO as the AI studio. This entry recognises the generated elements within a wider production involving direction, cinematography, editing, colour and sound.'),
}
scrape, reviewed, audit = [], [], []
for row in research:
    code = row['url'].rstrip('/').split('/')[-1]
    meta = {m['key']:m['value'] for m in row['meta']}
    source = meta.get('og:description','')
    if code not in selected:
        audit.append(dict(url=row['url'],status='not imported',reason='No explicit AI statement found in the reviewed caption',caption_metadata=source))
        continue
    title,category,description=selected[code]
    match = re.search(r' no (\w+ \d+, \d{4}): "(.*)"\.\s*$',source,re.S)
    if not match:
        raise ValueError(f'Missing publication date/caption for {code}')
    date=datetime.strptime(match[1],'%B %d, %Y').date().isoformat()
    caption=match[2]
    cover=meta['og:image']
    scrape.append(dict(url=row['url'],user_posted='belcrobelcro',date_posted=date+'T12:00:00Z',
                       description=description,original_caption=caption,thumbnail=cover,
                       post_content=[dict(type='Image',url=cover)]))
    reviewed.append(dict(url=row['url'],summary=title,artist_credit='BELCRO',category=category,
                         description=description,tools='',ai_disclosure='AI use explicitly declared by BELCRO in the source caption'))
    audit.append(dict(url=row['url'],status='selected',title=title,published_on=date,
                      ai_evidence=caption,approval='Creator supplied by the user on 2026-10-25'))
for name,data in [('belcro-scrape-en.json',scrape),('belcro-reviewed-en.json',reviewed),('belcro-curation-audit.json',audit)]:
    (root/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'{len(scrape)} selected; {len(audit)-len(scrape)} left unpublished.')
