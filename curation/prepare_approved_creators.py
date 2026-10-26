"""Build the reviewed batch for the three creators approved on 2026-10-25."""
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
records = json.loads((ROOT/'approved-creators-post-research.json').read_text(encoding='utf-8'))
film_evidence = 'https://humancentric.miketeevee.com/'
helmet_evidence = 'https://www.g42.ai/resources/news/g42-teamemirates-met-helmetverse-2026-seasontwo'
selected = {
    'DcxghuUxdDN': dict(
        title='The Regular', artist='Veronika Pell / Mindeye', username='__mindeye___', category='FILM',
        tools='Midjourney, Runway', editorial=False,
        description='A dark fairytale by Veronika Pell for HUMANCENTRIC, produced and curated by MikeTeevee. Working from a scene by Efthimis Filippou, Pell places women at the centre of the story and changes the gender of one of its main characters. The artist identifies Midjourney and Runway as her tools and dates the production to April 2026.',
        evidence=film_evidence),
    'DHUZ8B_Cny5': dict(
        title='Animated Portraits — Archive Studies', artist='Veronika Pell / Mindeye', username='__mindeye___', category='FILM',
        tools='Midjourney', editorial=True,
        description='An animated return to earlier portrait series by Veronika Pell. Revisiting her archive, the artist brings previous images into motion and uses them as a starting point for new ideas. The source identifies Midjourney and AI animation; no separate animation tool is specified. Editorial title assigned by the Atlas.'),
    'Dcwr4rGFzzF': dict(
        title='Mindeye — Portrait Metamorphoses', artist='Veronika Pell / Mindeye', username='__mindeye___', category='FILM',
        tools='Krea, Dreamina', editorial=True,
        description='An image and animation study by Veronika Pell, published under the name Mindeye. The artist credits Krea for the images and Dreamina for animation. The work continues her exploration of changing identities and surreal portraiture. Editorial subtitle assigned by the Atlas.'),
    'Dctf7nNvmb1': dict(
        title='Source Materials', artist='Veronika Pell / Mindeye', username='__mindeye___', category='FILM',
        tools='Midjourney, Runway', editorial=False,
        description='A moving-image study from Veronika Pell’s Source Materials series. The original publication identifies Midjourney for the images and Runway for animation.'),
    'DcrIXFvF7Ow': dict(
        title='The Fifth Wave', artist='Veronika Pell / Mindeye', username='__mindeye___', category='AI',
        tools='Krea', editorial=False,
        description='A portrait series by Veronika Pell, published as The Fifth Wave. The work explores the artist’s dreamlike, transforming visual language. Krea is explicitly identified in the original caption.'),
    'DcyrbvRsy76': dict(
        title='The Hunter', artist='Gizem Akdağ & Ege Berkina Akdağ', username='giz.akdag', category='FILM',
        tools='', editorial=False,
        description='An AI-assisted short film by Gizem Akdağ and Ege Berkina Akdağ for HUMANCENTRIC, produced and curated by MikeTeevee. The pair build a story around the events preceding an original scene by Efthimis Filippou, keeping its dialogue intact.',
        evidence=film_evidence),
    'DaiO7jijLlc': dict(
        title='Helmetverse — Tour de France Edition', artist='Gizem Akdağ / G42 / MET Helmets', username='uae_team_emirates', category='DESIGN',
        tools='', editorial=True,
        description='A special-edition cycling helmet designed with AI in collaboration with Gizem Akdağ, G42, MET Helmets and UAE Team Emirates-XRG. Inspired by movement, speed and the transition from data to light, the design was realised as a physical race helmet. AI involvement in the design is confirmed by G42; this does not describe the product photographs as AI-generated.',
        evidence=helmet_evidence),
}

scrape, reviewed, audit = [], [], []
for row in records:
    meta = {m['key']: m['value'] for m in row['meta']}
    url = meta.get('og:url') or row['url']
    code = url.rstrip('/').split('/')[-1]
    if code not in selected:
        continue
    item = selected[code]
    if item['username'] == 'blumquist_':
        raise ValueError('Rejected creator cannot be included')
    match = re.search(r' no (\w+ \d+, \d{4}): "(.*)"\.\s*$', meta.get('og:description',''), re.S)
    if not match:
        raise ValueError(f'Missing publication metadata: {code}')
    date = datetime.strptime(match[1],'%B %d, %Y').date().isoformat()
    cover = meta['og:image']
    disclosure = ('AI-assisted design confirmed by G42' if code == 'DaiO7jijLlc'
                  else 'AI filmmaking confirmed by the artists and HUMANCENTRIC' if code == 'DcyrbvRsy76'
                  else 'Generative tools identified in the source caption')
    scrape.append(dict(url=url, user_posted=item['username'], date_posted=date+'T12:00:00Z',
                       original_caption=match[2], description=item['description'], thumbnail=cover,
                       post_content=[dict(type='Image',url=cover)]))
    reviewed.append(dict(url=url, summary=item['title'], artist_credit=item['artist'],
                         category=item['category'], description=item['description'], tools=item['tools'],
                         ai_disclosure=disclosure, title_is_editorial=item['editorial']))
    audit.append(dict(url=url,title=item['title'],artist=item['artist'],published_on=date,
                      tools=item['tools'],ai_evidence=item.get('evidence') or url,
                      evidence_excerpt=match[2],title_is_editorial=item['editorial'],
                      approval='User approved Mindeye, Gizem Akdag and Ege Berkina; rejected Blumquist on 2026-10-25'))
if len(scrape) != len(selected):
    raise ValueError(f'Expected {len(selected)} unique selections, got {len(scrape)}')
for name, data in [('approved-creators-scrape-en.json',scrape),
                   ('approved-creators-reviewed-en.json',reviewed),
                   ('approved-creators-curation-audit.json',audit)]:
    (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

shortlist_path=ROOT/'profile-shortlist-awaiting-approval.json'
shortlist=json.loads(shortlist_path.read_text(encoding='utf-8'))
for profile in shortlist:
    profile['status']='rejected by user' if profile['handle']=='blumquist_' else 'approved by user'
    profile['reviewed_on']='2026-10-25'
shortlist_path.write_text(json.dumps(shortlist,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
watchlist=ROOT/'creator-watchlist.txt'
urls=watchlist.read_text(encoding='utf-8').splitlines()
for handle in ['__mindeye___','giz.akdag','egeberkina']:
    url=f'https://www.instagram.com/{handle}/'
    if url not in urls: urls.append(url)
watchlist.write_text('\n'.join(urls)+'\n',encoding='utf-8')
print(f'Prepared {len(scrape)} unique projects. Three creators approved; Blumquist excluded.')
