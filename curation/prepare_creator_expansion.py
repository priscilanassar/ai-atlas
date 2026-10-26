"""Build a reviewed import batch from public-page research captured on 2026-10-25."""
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
rows = json.loads((ROOT / 'creator-normalized-research.json').read_text(encoding='utf-8'))
existing = set(json.loads((ROOT / 'existing-instagram-codes.json').read_text()))
# Editorial titles and descriptions; quotations and original captions are not used as public copy.
editorial = {}
for line in """
Dew1-qWkWXi|Sculpting Fabric into Emotion|An AI-labelled textile image study by Hanna Inaiáh, extending her exploration of fabric, surface and visual expression.
DesCfBtoCkP|Women, Wool, Wings and Other Living Things|A visual study bringing women, wool and winged forms into the same imagined world, by Bruna Bismara and Touch of Oddity.
DecRTY3kVPI|Red Frequency|A study of beauty, motion and high-volume red, published by Bruna Bismara with Touch of Oddity.
DeXUmqBoPtU|Petals, Pulse, Pigment|Bruna Bismara explores the relationship between petals, perfume, pigment and visual intensity.
DehgUYQILoU|A Wardrobe of Its Own|A speculative fashion study that combines glossy surfaces, fungal forms and the idea of a wardrobe growing wild.
DdoMUs9kTYv|Chromophilia|A colour-led visual interruption within the rhythms of the city, by Bruna Bismara and Touch of Oddity.
DdrJ3mrkbAQ|Something Wild, Something Mine|A visual experiment around drift, vertigo and a renewed sense of feeling.
DdkDz3vAQJy|Not Everything Beautiful Is Real|Artificial plants, ceramics and iridescent surfaces form a quiet study between nature and the unreal.
DdJa6XhkVWl|The Warmth of Being Wild|An imagined visual world centred on nature, growth and the freedom to unfold.
DcvwNMQgD01|Bellows|YZA Voku's visual experiment originally titled Fuelle, presented here with an English editorial translation.
DernCMkNn07|Static Seed|A moving-image study by YZA Voku, shared as an AI-labelled publication.
Db54kbct-_B|Just a Coincidence|A visual experiment by YZA Voku exploring the possibilities of constructed imagery.
DePOUDyDZIA|Pyrrhic|An AI-labelled work by YZA Voku, originally published as Pírrica. The title is translated for the English Atlas.
DdjgBOUkSEy|Saltpetre|A visual work by YZA Voku, originally titled Salitre and presented here with an English editorial translation.
DblDKFbDQhv|38°25′00″N 20°40′00″E|A visual experiment by YZA Voku named after a geographic coordinate. The title does not establish the artist's location.
DehHrF7Dbqg|Off the Statement|A moving-image experiment by director YZA Voku, labelled as AI content in its source publication.
DdEkS8nkeNs|Golden Ground|An AI-labelled visual study by YZA Voku, originally published as Golden Ground.
DbGaOT8CLbu|The Uncertain Experiment|YZA Voku's visual study of precision, models and uncertainty. This is a shortened editorial title.
DadBxpPN2qk|Rules We Accept|A film directed by YZA Voku reflecting on the rules that make a competition possible. The title is editorial.
DQCNAJZDFS_|Theatre Without an Audience|A visual work by YZA Voku about a theatre without an audience and a city without a voice. The title is shortened for the Atlas.
Det7Fs6RlC-|Spark|A short visual experiment by Xe, published as Spark with an AI content label.
DeJ2EQvOa3a|Play|A moving-image experiment by Xe that credits Higgsfield in the original caption.
DcwsF07J3uW|Star Fit|Floam World imagines a star-shaped fashion look in a playful study of inflatable clothing and digital characters.
DTGuC-oCagL|Smilees — Everything's Fine Face|The second Smilees episode turns the pressure to appear cheerful into surreal character design and fashion satire.
De2bdSDJ_jl|Modern Warfare — Slime Edition|A surreal fashion parody by Floam World, populated by the creator's original characters.
DYXPk7Guwr6|Floam World — Dior Cruise|A Floam World fashion interpretation inspired by Dior Cruise 2027. This is an artist interpretation; no commission is asserted.
DTjwVYDjjKj|Bouquet — A Floam Interpretation|A surreal fashion film inspired by Gentle Monster's Bouquet collection and reimagined through Floam World's character language.
DefAACziaaW|Floam World Dailies|A daily visual experiment from Floam World's expanding universe of surreal characters.
DdgwaVOjUAD|Floam World — Proenza Schouler|A fashion-inspired character story referencing Proenza Schouler by Rachel Scott and a trip to the Rubin Museum of Art.
DdcSfZdJBLK|New York Dance Break|A playful AI-fashion dance interlude populated by Floam World's surreal characters.
De6v-fgGbqE|Attack on Tempo|An unofficial metronome-figure concept by NVMHYUK inspired by Attack on Titan. It is a speculative design, not an available product.
DewVeqOKUXg|Old Buds — Denture Wireless Earbuds|A speculative design by NVMHYUK combining dentures and wireless earbuds. The work is a concept rather than a retail product.
DeZHwTPzIT6|Employee of the Month — Shizuka|A fictional headpiece campaign set in a Japanese bank in 1996, conceived and visualised by NVMHYUK.
DaoCd9DOu2V|Hope You're Doing Well|An AI-labelled moving-image experiment by artist and visual director Doopiidoo.
DQcXvxsiDWc|Cloud in the Pants|An experimental short by Doopiidoo, published with an AI content label.
Ddi8D_6ugwK|Bottomless Puddle|A moving-image work by Doopiidoo, published as Bottomless Puddle. Related posts from the same project are kept out of the globe.
DdZl4nUOhvx|Patternson|Doopiidoo's short film for HUMANCENTRIC, an anthology in which eight artists interpret an original scene by Efthimis Filippou. The series is created by MikeTeevee.
Ddo0JX-sk3r|The Odyssey — An Imaginary Rollercoaster|If Only imagines a rollercoaster inspired by The Odyssey, using generative tools credited in the source.
DcJIN-kMvNN|Dive into a Masterpiece|If Only transforms the idea of entering a painting into an AI film, created in collaboration with Artlist.
DXlwDjyDG8n|Delicate — If Only Love Always Won|An AI film by If Only, created with Dreamina and Seedance 2.0.
DVQq4TzDAp3|If Only Art Came to Life|A moving-image artwork by If Only exploring paintings as living worlds, made in partnership with Artlist.
DQuNlXpjMmE|The Luxury Bus Parade|An imagined parade of luxury-brand buses through Paris, created by If Only using a combination of generative and finishing tools.
De35knght7L|Horror Movies Take Over Paris|If Only reimagines Paris through the visual language of horror cinema, with AI generation credited to Dreamina.
DexB5PhvhhW|Art to a Piano Melody|If Only explores artwork coming alive to piano music, with generative tools identified in the original publication.
DerRe5iOJmu|Inside the Further|A speculative cinematic journey inspired by the world of Insidious, created by If Only with Dreamina.
Deei4PHRpQt|Paradise, Unlocked|An imagined paradise by If Only, developed with Midjourney and Dreamina.
DePKnN6sYs5|A Good Time to Be Parisian|An AI-generated visual story set around an imagined Paris, by If Only.
DeHeaZVBCAE|Terrifier — An Imaginary Rollercoaster|A speculative theme-park ride inspired by Terrifier, imagined by If Only with Dreamina. No official attraction is implied.
DaNUQ3CMn0v|If Only Art Came to Life — Part Three|The third episode of If Only's series imagining entry into artworks, published in collaboration with Artlist.
""".strip().splitlines():
    code, title, description = line.split('|', 2)
    editorial[code] = (title, description)

untitled_codes = {'Dbvy4k1qk4a', 'DeO-TbdjolZ', 'DeMbHHSDn5C', 'DeKjxssjvir', 'DeEzbCNOy4I', 'DdwU4DbuxbF', 'DdMUGStKWkv'}
selected = []
curation = []
audit = []
for p in rows:
    code = p['url'].rstrip('/').split('/')[-1]
    if code in existing or code not in editorial and code not in untitled_codes:
        audit.append({'url': p['url'], 'selected': False, 'reason': 'Already published, repeated project, non-art content or insufficient project-level AI evidence.'})
        continue
    # Profile thumbnail alt text supplies the post date even when the caption is absent.
    match = re.search(r'on ([A-Z][a-z]+ \d{2}, \d{4})', p.get('alt') or '')
    published = datetime.strptime(match[1], '%B %d, %Y').isoformat() + 'Z' if match else p.get('date')
    if code in untitled_codes:
        title = 'Untitled Motion Study — ' + published[:10]
        description = "An untitled moving-image experiment by Doopiidoo. The original publication displays an AI content label. The Atlas uses an editorial title based on its publication date."
    else:
        title, description = editorial[code]
    label = 'Conteúdo de IA' in p['text'][:500]
    evidence = 'AI content label displayed on the original publication' if label else 'Generative tools identified in the source caption'
    author = p['url'].split('/')[3]
    artist = {'brubismara': 'Bruna Bismara / Touch of Oddity', 'hannainaiah': 'Hanna Inaiáh', 'yzavoku': 'YZA Voku', 'xeocho': 'Xe', 'floam.world': 'Floam World', 'nvmhyuk': 'NVMHYUK', 'doopiidoo': 'Doopiidoo', 'ifonly.ai': 'If Only'}.get(author, '@' + author)
    caption = p['caption'] if p.get('author') == author else ''
    tools = '; '.join(name for pattern, name in [('midjourney', 'Midjourney'), ('higgsfield', 'Higgsfield'), ('dreamina', 'Dreamina'), ('seedance', 'Seedance'), ('kling', 'Kling'), ('topaz', 'Topaz'), ('nano banana', 'Nano Banana'), ('artlist', 'Artlist')] if pattern in caption.lower())
    selected.append({'url': p['url'], 'user_posted': author, 'description': description, 'original_caption': caption, 'date_posted': published, 'thumbnail': p['image'], 'post_content': []})
    curation.append({'url': p['url'], 'summary': title, 'description': description, 'artist_credit': artist, 'category': 'FILM' if '/reel/' in p['url'] else 'AI', 'tools': tools, 'ai': 'Declarado na legenda' if not label else '', 'ai_disclosure': evidence})
    audit.append({'url': p['url'], 'selected': True, 'evidence': evidence, 'title_is_editorial': True})
(ROOT / 'creator-expansion-scrape-en.json').write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT / 'creator-expansion-reviewed-en.json').write_text(json.dumps(curation, ensure_ascii=False, indent=2), encoding='utf-8')
(ROOT / 'creator-expansion-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(selected)} new unique posts selected.')
