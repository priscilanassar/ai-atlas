"""Build only the newly approved references; never republish older batches."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
research = json.loads((ROOT / 'requested-posts-research-2.json').read_text(encoding='utf-8'))
confirmed = 'AI use confirmed by the Atlas curator; tools not disclosed'
entries = [
    ('We Are the Noise', 'Infrarouge / Anthony Tournadre', '___infrarouge', '2025-07-15', 'AI',
     'A visual series by Infrarouge, published as “We Are The Noise” and credited to @dixon_. The work brings an uncanny, post-photographic perspective to the Atlas.', '', confirmed),
    ('You Glitched into This', 'Infrarouge / Anthony Tournadre', '___infrarouge', '2025-12-05', 'AI',
     'A post-photographic image series by Infrarouge exploring a distorted, unsettling visual world. The original publication identifies Midjourney as part of the process.', 'Midjourney', 'Midjourney identified in the source caption'),
    ("It’s Important to Have Perspective", 'Bernardo Martins', 'figa.link', '2026-04-28', 'FASHION',
     'A fashion and portrait study by Bernardo Martins, published under the caption “It’s important to have perspective.” Selected for its approach to beauty, proportion and altered identity.', '', confirmed),
    ('Tower — Backstage', 'Bernardo Martins / LIMTRF', 'figa.link', '2026-03-25', 'FASHION',
     'A backstage publication from the Tower project, shared by Bernardo Martins and LIMTRF with credits to A Magazine Curated By and Rick Owens. The Atlas curator confirms AI involvement in the project; the source credits the backstage imagery to LIMTRF. This is a record of the creative process, not a claim that every backstage photograph is fully generated.', '', confirmed),
    ('Elevator Outfit Transformations', 'Priscila Nassar', 'priscila.nassar', '2026-05-27', 'FILM',
     'An AI-assisted fashion motion study in which an elevator mirror portrait becomes a sequence of changing outfits. Graphic shapes, bright colour and floral motifs transform the everyday setting. Editorial title assigned by the Atlas; the original reel has no caption.', '', confirmed),
]
scrape, curated, audit = [], [], []
for row, (title, artist, username, date, category, description, tools, disclosure) in zip(research, entries):
    meta = {m['key']: m['value'] for m in row['meta']}
    caption_meta = meta.get('og:description', '')
    caption = caption_meta.split(': "', 1)[1].rsplit('".', 1)[0] if ': "' in caption_meta else ''
    cover = meta['og:image']
    if username == 'priscila.nassar' and (ROOT/'clean-priscila-cover.json').is_file():
        cover = json.loads((ROOT/'clean-priscila-cover.json').read_text(encoding='utf-8'))['url']
    scrape.append(dict(url=row['url'], user_posted=username, date_posted=date+'T12:00:00Z',
                       description=description, original_caption=caption, thumbnail=cover,
                       post_content=[dict(type='Image', url=cover)]))
    curated.append(dict(url=row['url'], summary=title, artist_credit=artist, category=category,
                        description=description, tools=tools, ai_disclosure=disclosure))
    audit.append(dict(url=row['url'], title=title, published_on=date,
                      ai_evidence='Publisher caption: #midjourney' if tools else 'User confirmed AI use in this conversation on 2026-10-25',
                      title_basis='Editorial title' if username=='priscila.nassar' or title.startswith('Tower') else 'Source caption',
                      tools=tools, approval='Explicitly requested and confirmed by user'))

scoria = next(r for r in json.loads((ROOT/'creator-normalized-research.json').read_text(encoding='utf-8'))
              if '/Ddb_6hoAkyi/' in r.get('url',''))
description = ('Scoria is Infrarouge’s short film for HUMANCENTRIC, an anthology produced and curated by MikeTeevee. '
               'Working from an original scene by Efthimis Filippou, the artist uses rain, cold light and mineral textures '
               'to shape a psychological world. The film combines generated imagery with deliberate editing and image degradation.')
scrape.append(dict(url=scoria['url'], user_posted='___infrarouge', date_posted='2026-09-18T12:00:00Z',
                   description=description, original_caption=scoria['caption'], thumbnail=scoria['image'],
                   post_content=[dict(type='Image',url=scoria['image'])]))
curated.append(dict(url=scoria['url'], summary='Scoria', artist_credit='Infrarouge / Anthony Tournadre',
                    category='FILM', description=description, tools='',
                    ai_disclosure='AI filmmaking documented in the artist’s HUMANCENTRIC interview'))
audit.append(dict(url=scoria['url'], title='Scoria', published_on='2026-09-18',
                  ai_evidence='https://www.art-magazine.ai/artist-directory/feature/humancentric-eight-films-one-script',
                  title_basis='Artist’s original film title', tools='', approval='Similar work by an artist in the user’s supplied references'))
for name, data in [('requested-references-scrape-en.json',scrape),
                   ('requested-references-reviewed-en.json',curated),
                   ('requested-references-audit.json',audit)]:
    (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Prepared {len(scrape)} references.')
