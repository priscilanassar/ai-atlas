"""Reviewed additions from existing creators, excluding every previously published code."""
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
rows = json.loads((ROOT/'globe-expansion-post-research.json').read_text(encoding='utf-8'))
previous = set(json.loads((ROOT/'globe-expansion-previously-published.json').read_text(encoding='utf-8')))
acid_evidence = 'https://br.linkedin.com/company/theacidtimes'
oddity_evidence = 'https://www.instagram.com/touchofoddity/'
figa_evidence = 'https://www.coeval-magazine.com/coeval/bernardo-martins'
selections = {
    'DehVhaJRvjE': ('Mr. Cucumber — Episode 01', 'The Acid Times / Bruno Zampoli', 'FILM',
        'An absurdist short from The Acid Times introducing Mr. Cucumber, a fictional character whose attempts to help create problems of their own.'),
    'De45m5YgGk3': ('Animal Instincts, Human Problems', 'The Acid Times / Bruno Zampoli', 'FILM',
        'A surreal visual series bringing animal instincts into familiar human situations. The studio’s caption pairs animal behaviour with everyday problems.'),
    'Dep-wWejnDF': ('Above Everything', 'The Acid Times / Bruno Zampoli', 'AI',
        'An exaggerated satirical scene from The Acid Times, using scale and an impossible public spectacle to turn an everyday phrase into a visual provocation.'),
    'Dem2y0WRJym': ('Acid Room', 'The Acid Times / Bruno Zampoli', 'FILM',
        'An imaginary dance floor brings seven headliners and seven visual worlds together. This is a fictional music scene from the studio’s Acid Room series.'),
    'Deb67J1juIi': ('Pressed by Acid', 'The Acid Times / Bruno Zampoli', 'AI',
        'A surreal study of pressure, compression and familiar objects, published as part of the studio’s Prensado da Acid series.'),
    'DeNdwFdDpgK': ('Acid Wishlist', 'The Acid Times / Bruno Zampoli', 'AI',
        'A collection of imaginary, deliberately impractical products. Acid Wishlist borrows the language of shopping and collectibles to build objects that exist as visual jokes.'),
    'DeE5fl5O12O': ('The Democracy Cake', 'The Acid Times / Bruno Zampoli', 'AI',
        'A satirical editorial image from The Acid Times, turning the idea of a democracy cake into an excessive visual confection.'),
    'Dd2N8AvxH9g': ('Street Non-View', 'The Acid Times / Bruno Zampoli', 'FILM',
        'An imaginary street-view sequence built around scenes the studio’s fictional camera operators never recorded. A playful interruption of documentary-looking everyday imagery.'),
    'DduirRNDirK': ('Pause for Delirium', 'The Acid Times / Bruno Zampoli', 'AI',
        'A surreal pause in the everyday: an imagined flying-saucer taxi turns an ordinary street into speculative urban transport.'),
    'Ddpag0KDoIl': ('Nothing to Declare', 'The Acid Times / Bruno Zampoli', 'AI',
        'An illustrative visual fiction published by The Acid Times under the caption Nothing to Declare. Familiar travel imagery becomes a scene of deliberate absurdity.'),
    'Dee_jHpIEUE': ('A Kind of Other', 'Bruna Bismara / Touch of Oddity', 'FASHION',
        'A soft-coloured portrait series exploring a presence that is almost earthly: part flesh, part fiction, and not yet named. Created by Bruna Bismara with Touch of Oddity.'),
    'Dcgt61JEX_A': ('Made to Melt', 'Bruna Bismara / Touch of Oddity', 'AI',
        'Soft objects of desire become the subject of an imagined product study. The series explores tactile surfaces, melting forms and sculptural colour.'),
    'DdCFE9fkWJW': ('Thick Skin', 'Bruna Bismara / Touch of Oddity', 'FASHION',
        'Skin and pigment become material for a bold beauty study. Thick Skin pushes surface, colour and texture beyond the familiar limits of portraiture.'),
    'DbtOb42kc73': ('Freakats', 'Bruna Bismara / Touch of Oddity', 'AI',
        'Floral, fungal felines form a strange imagined species. Bruna Bismara combines soft fur, botanical growth and an unmistakably feline attitude.'),
    'DeKKhUFANxZ': ('Inner Thoughts', 'Bernardo Martins', 'AI',
        'A portrait study by Bernardo Martins, published with a caption about the inner thoughts he faced during the preceding month. An unsettling, intimate extension of his generative image practice.'),
    'Db3kGKKgIDM': ('Non-Human Agony Factory', 'Bernardo Martins', 'AI',
        'An imagined figure becomes a study of the body, expression and unease. Published by Bernardo Martins under the title Non Human Agony Factory.'),
    'DYw1t_YgKUo': ('Summer Heat', 'Bernardo Martins', 'FASHION',
        'A synthetic portrait by Bernardo Martins exploring the feeling of summer heat through a body suspended between beauty, discomfort and exaggeration.'),
    'DbLn0VMiBoh': ('Back', 'Bernardo Martins', 'AI',
        'An image by Bernardo Martins realised as an aluminium print and presented by Studio Iron. The publisher identifies the artist’s transition from photography and design into AI image-making.'),
    'DYfMMaGjJxJ': ('Save Face', 'Bernardo Martins', 'DESIGN',
        'Bernardo Martins brings his generative portraits into print with Save Face. This publication documents the testing, printing and binding of a physical book of his imagined faces.'),
}
scrape, reviewed, audit = [], [], []
for row in rows:
    meta = {m['key']:m['value'] for m in row['meta']}
    url = meta.get('og:url') or row['url']
    code = url.rstrip('/').split('/')[-1]
    if code not in selections:
        continue
    if code in previous:
        raise ValueError(f'Refusing to restore a previously published or deleted work: {code}')
    title, artist, category, description = selections[code]
    match = re.search(r'(?:^| - )([\w.]+) no (\w+ \d+, \d{4}): "(.*)"\.\s*$',meta.get('og:description',''),re.S)
    if not match:
        raise ValueError(f'Missing caption or publication date: {code}')
    username, date_text, caption = match.groups()
    date = datetime.strptime(date_text,'%B %d, %Y').date().isoformat()
    if username == 'blumquist_':
        raise ValueError('Rejected creator')
    if row['profile'] == 'theacidtimes':
        evidence = acid_evidence
        disclosure = 'AI editorial practice declared by The Acid Times; project tools not disclosed'
        basis = 'Studio’s public AI-production statement, source publication and visual review'
    elif row['profile'] == 'touchofoddity':
        evidence = oddity_evidence
        disclosure = 'Published by Touch of Oddity, Bruna Bismara’s AI studio; tools not disclosed'
        basis = 'Work appears in the artist’s AI studio portfolio; source caption and visual review'
    else:
        evidence = figa_evidence
        disclosure = 'Generative portrait practice documented by the artist; project tools not disclosed'
        basis = 'Artist interview documents AI portraiture; the selected work was reviewed against that practice'
        if code == 'DYfMMaGjJxJ':
            evidence = 'https://www.introe.co/read/figa-link-is-rewriting-the-face-of-digital-beauty'
            basis = 'Save Face is documented as a book of the artist’s AI-generated portraits'
    cover = meta['og:image']
    scrape.append(dict(url=url,user_posted=username,date_posted=date+'T12:00:00Z',
                       description=description,original_caption=caption,thumbnail=cover,post_content=[]))
    reviewed.append(dict(url=url,summary=title,artist_credit=artist,category=category,
                         description=description,tools='',ai_disclosure=disclosure))
    audit.append(dict(url=url,title=title,artist=artist,published_on=date,ai_evidence=evidence,
                      evidence_basis=basis,source_caption=caption,tools_disclosed=False,
                      approval='More projects requested by user; artists previously supplied or already curated',
                      title_is_editorial=title not in ('Acid Room','A Kind of Other','Made to Melt','Thick Skin','Freakats','Back','Summer Heat','Save Face')))
if len(scrape) != len(selections):
    raise ValueError(f'Expected {len(selections)} unique works; got {len(scrape)}')
for name,data in [('globe-expansion-scrape-en.json',scrape),
                  ('globe-expansion-reviewed-en.json',reviewed),
                  ('globe-expansion-curation-audit.json',audit)]:
    (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Prepared {len(scrape)} new works, excluding deleted works, duplicate series and the rejected creator.')
