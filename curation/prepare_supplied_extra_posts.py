"""The eight Instagram references explicitly supplied by the curator."""
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
research = json.loads((ROOT/'supplied-extra-post-research.json').read_text(encoding='utf-8'))
mayara_evidence = 'https://www.behance.net/gallery/199780269/Album-de-Desesquecimentos?locale=en_US'
entries = {
    'DZfJfUvRwUR': ('Album of Unforgetting — A Kiss', 'Mayara Ferrão', 'AI', '',
        'An imagined scene of affection from Mayara Ferrão’s Album of Unforgetting. The artist uses AI to construct intimate representations of Black and Indigenous women and question the absences in historical archives. This is a speculative artwork, rather than a documentary photograph.'),
    'DV-HZkEjdDL': ('Album of Unforgetting — Bridal Flowers', 'Mayara Ferrão', 'AI', '',
        'A bridal scene from Mayara Ferrão’s Album of Unforgetting, accompanied by a reflection on flowers, luminous presence and love. AI-generated imagery gives form to an imagined intimate memory. Editorial English title assigned by the Atlas.'),
    'DTsqGHOkZaf': ('Album of Unforgetting — Fragments', 'Mayara Ferrão', 'AI', '',
        'A fragmentary image from Mayara Ferrão’s Album of Unforgetting. The series uses AI-generated, archive-like imagery to imagine presences and relationships missing from historical visual records. This entry represents the artist’s January 2026 publication; its subtitle is editorial.'),
    'DUQTgKUDuuU': ('February 2 — Rio Vermelho Memories', 'Bruno Zambelli', 'FILM', '',
        'Bruno Zambelli revisits childhood memories of February 2 in Rio Vermelho, Salvador. Flowers, water and ceremonial imagery become elements in a visual study of the celebration of Yemanjá, expanding an earlier exploration of those memories.'),
    'DcCXZSIO0cp': ('Disruptive Beauty', 'Bruno Zambelli', 'FILM', '',
        'A speculative beauty portrait by Bruno Zambelli, pairing pale, sculptural hair with gold-toned detail and an unfamiliar visual presence. The original caption suggests a model that will unsettle expectations. Editorial title assigned by the Atlas.'),
    'DF6Cpc8S1yo': ('Offerings for Yemanjá — Cachoeira', 'Bruno Zambelli', 'FILM', 'Midjourney, Kling',
        'Offerings to Yemanjá in Cachoeira, Bahia, inspire a different palette and a new visual interpretation by Bruno Zambelli. The source caption explicitly identifies Midjourney and Kling as part of the process.'),
    'DWEjLNxDS5s': ('Terrible Beauty — Casting Archive', 'Iago Cruz', 'FASHION', '',
        'An avant-garde digital fashion study situated between the familiar and the strange. Iago Cruz explores the uncanny valley through an imagined casting portrait and a deliberately unsettling approach to beauty. Editorial English title based on the publication’s series tags.'),
    'DRx4_axDUtl': ('Theory of Nothing — Visual Studies', 'Iago Cruz', 'FASHION', '',
        'Image studies by Iago Cruz exploring texture, movement and visual possibilities across fashion, design, architecture and editorial image-making. In the original caption, the artist describes AI as a way to test ideas and construct scenes that previously existed only in his imagination.'),
}
scrape, reviewed, audit = [], [], []
for row in research:
    code = row['url'].rstrip('/').split('/')[-1]
    title, artist, category, tools, description = entries[code]
    meta = {m['key']:m['value'] for m in row['meta']}
    match = re.search(r'(?:^| - )([\w.]+) no (\w+ \d+, \d{4})(?:: "(.*)"\.\s*)?$',meta['og:description'].strip(),re.S)
    if not match:
        raise ValueError(f'Missing publisher/publication date: {code}')
    username,date_text,caption = match.groups()
    date=datetime.strptime(date_text,'%B %d, %Y').date().isoformat()
    url=meta.get('og:url') or row['url']
    if username=='mayaraferrao':
        disclosure='AI use documented by the artist for Album of Unforgetting'
        evidence=mayara_evidence
    elif tools:
        disclosure='Midjourney and Kling identified in the source caption'
        evidence=url
    elif code=='DRx4_axDUtl':
        disclosure='AI image-making explicitly described in the source caption'
        evidence=url
    elif username=='iagocz':
        disclosure='Digital fashion study by AI image-maker Iago Cruz; tools not disclosed'
        evidence='https://www.instagram.com/iagocz/p/DRx4_axDUtl/'
    else:
        disclosure='Visual study by AI artist Bruno Zambelli; project tools not disclosed'
        evidence='https://www.instagram.com/brunozambelli/'
    scrape.append(dict(url=url,user_posted=username,date_posted=date+'T12:00:00Z',
                       description=description,original_caption=caption or '',thumbnail=meta['og:image'],post_content=[]))
    reviewed.append(dict(url=url,summary=title,artist_credit=artist,category=category,description=description,
                         tools=tools,ai_disclosure=disclosure))
    audit.append(dict(url=url,title=title,artist=artist,published_on=date,ai_evidence=evidence,
                      tools=tools,original_caption=caption or '',title_is_editorial=True,
                      approval='Post explicitly supplied by the user on 2026-10-25',
                      series='Album of Unforgetting' if username=='mayaraferrao' else '',
                      note='Distinct selected images from the same series keep their own original publication links.'))
for name,data in [('supplied-extra-scrape-en.json',scrape),('supplied-extra-reviewed-en.json',reviewed),('supplied-extra-curation-audit.json',audit)]:
    (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
watchlist=ROOT/'creator-watchlist.txt'
profiles=watchlist.read_text(encoding='utf-8').splitlines()
for handle in ['mayaraferrao','brunozambelli','iagocz','giz.akdag']:
    url=f'https://www.instagram.com/{handle}/'
    if url not in profiles: profiles.append(url)
watchlist.write_text('\n'.join(profiles)+'\n',encoding='utf-8')
print(f'Prepared {len(scrape)} user-supplied posts and saved the approved creator profiles.')
