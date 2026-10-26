"""Publish this reviewed batch only; reruns preserve existing curated projects."""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE/'.venv/Lib/site-packages'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from django.db import transaction
from archive.models import Project, CurationSubmission
from PIL import Image

# English editorial descriptions; tool names are included only when disclosed.
EDITORIAL = {
 'Dcv5WIxMBan': ('Potato Swan Dream', 'Josefina Sierra Guzmán', '', 'AI',
   'A swan assembled from potatoes rests among white flowers on a bed. Josefina Sierra Guzmán transforms an everyday ingredient into a tender, improbable creature. English curatorial title translated from the original publication.'),
 'Deufwm8CACa': ('Vampire Cats', 'Oddatide', 'OpenArt', 'AI',
   'Fantastical cats combine sharp fangs, bright fur and a playful Halloween mood. Oddatide explicitly credits OpenArt for this character study, bringing an uncanny edge to otherwise familiar animal portraits.'),
 'DePPoA1mPSN': ('Dancing Balloons', '@oasis.seo.ai', 'Kling', 'AI',
   'Transparent balloon figures form a small, animated ensemble. The work turns inflated bodies and reflected light into a playful choreography. The artist identifies Kling and restricts commercial use and modification.'),
 'DezTQLAmDQ-': ('Somewhere Online, Christmas', '@oasis.seo.ai', 'Higgsfield; Soul', 'AI',
   'Christmas becomes an imagined online environment framed by a nostalgic computer interface. The artist credits Higgsfield and Soul for this synthetic seasonal world and states restrictions on commercial use and modification.'),
 'De6AoTjG1vk': ('Pioneer CDJ-3000X — Silver Ornament Study', 'BECCU Studio', 'Krea', 'DESIGN',
   'An imagined Pioneer CDJ-3000X is covered in ornate silver relief. Created with Krea, the study treats a familiar piece of music equipment as a decorative object. Presented as a creative concept, not an announced product.'),
 'Ddt5Mt0BmUi': ('The Tea Ceremony', 'Ripe Visuals', '', 'AI',
   'A stylised figure in patterned clothing appears within a quiet tea setting. Published as Chanoyu, the work uses a cinematic, illustrated visual language. The creator identifies it as AI art without naming the tools.'),
 'De4WDWSjKcv': ('On Fire', 'Gizem Akdağ', '', 'AI',
   'Scarlet, flame-like forms rise above a field of wildflowers beneath a clear blue sky. Gizem Akdağ builds an impossible encounter between a pastoral landscape and an intensely coloured figure. Tools are not disclosed.'),
 'DaMp5EnDBJs': ('The Giraffe Snail', 'Studio Saint Blaise', '', 'AI',
   'A giraffe and a snail merge into an invented animal, pairing a long spotted neck with a rounded shell. The artist identifies the work as AI-generated and plays with the conventions of natural-history imagery.'),
 'DYeptCFjRE6': ('Zara — Bags in Motion', 'Maria Homs', '', 'FASHION',
   'Handbags become the focus of an AI content study for Zara, combining product imagery and moving urban scenery. Published by Dazzle AI, the source credits Maria Homs for AI production. English curatorial title assigned by the Atlas.'),
 'DWWvZAWjavc': ('Desigual — Product in Bloom', 'Dazzle AI', '', 'FASHION',
   'A sculptural floral form anchors an AI content project for Desigual. The publisher identifies product integration and animation as part of the process. The source does not specify the generation tools.'),
 'Deu_bMmhW7L': ('Halloween Time Machine', '@yusoncho', 'Higgsfield', 'AI',
   'Surreal clock imagery and playful transformations turn Halloween into an imagined journey through time. The artist explicitly credits Higgsfield for the moving-image work.'),
 'De7KySARB0c': ('Retina Timeout', 'Katsukokoiso', 'Higgsfield; Seedance 2.5; Krea K2; ChatGPT; Suno; Topaz', 'AI',
   'Screens and synthetic bodies occupy a dark, disorienting visual space. This experimental film reflects on mediated perception and digital overload. The artist discloses image, animation, music and enhancement tools in the original credits.'),
 'DZXJGYEgWEz': ('Lotus Life, Vol. 2', '@woosuummin', '', 'AI',
   'A pink lotus becomes part of an imagined urban encounter involving figures and a scooter. The artist describes this second Lotus Life instalment as an AI creation. Specific production tools are not disclosed.'),
 'DdPQWeoMW6h': ('The Beauty of Abandoned Things', 'Josefina Sierra Guzmán', '', 'AI',
   'An ordinary cleaning object sits within an unfamiliar, soft-textured environment. Josefina Sierra Guzmán finds a strange tenderness in discarded domestic things. English curatorial title translated from the original caption.'),
 'Dc_PaJ3slfq': ('Six Wet Pigeons on a Fax Machine', 'Josefina Sierra Guzmán', '', 'AI',
   'Wet pigeons become the protagonists of an improbable office scene. The publication pairs familiar birds with obsolete communication technology, combining domestic observation and visual absurdity. English title translated from the source caption.'),
 'DclzvsvjJkp': ('Candy-Coloured Cats', 'Oddatide', '', 'AI',
   'A brightly coloured feline portrait turns soft fur into an exaggerated field of colour. The work extends Oddatide’s playful animal imagery. The publication carries Instagram’s AI-content label; tools are not specified.'),
 'DU1F6bajIbv': ('Fire Horses — Lunar New Year', 'Oddatide', '', 'AI',
   'Flame-covered horses mark the Lunar New Year in a series organised around birthday months. The artist transforms the zodiac animal through changing colour and fiery material effects. English curatorial title based on the source caption.'),
 'Dc5x8-HNuSV': ('Cloud Gathering', '@oasis.seo.ai', 'Kling', 'AI',
   'Clouds become small, tangible objects within a familiar garden setting. A figure on a ladder makes the impossible activity feel almost domestic. The artist credits Kling and states restrictions on commercial use and modification.'),
 'DdJb0SnNlCE': ('Welcome to My Home', '@oasis.seo.ai', 'Kling', 'AI',
   'A small, fantastical house occupies a wooded clearing. Bright surfaces and an unusual building shape turn the familiar idea of home into a storybook environment. The artist identifies Kling and restricts commercial use and modification.'),
 'DZyF1X2knXG': ('Chrome Hearts × Porsche — Concept Car', 'BECCU Studio', 'Krea', 'DESIGN',
   'An imagined Porsche pairs decorative metalwork with custom headlights in a Chrome Hearts-inspired concept. The creator identifies Krea as the tool. This speculative design is not presented as an official collaboration between the brands.'),
 'DbWQDWfiLGr': ('Bedazzled Helmets', 'BECCU Studio', 'Krea', 'DESIGN',
   'Decorative helmets become studies in colour, shine and embellished surfaces. BECCU Studio credits Krea for the imagined designs, turning protective equipment into highly ornamental objects.'),
 'Dd4MatXO_tk': ('Textile Motion', 'Ripe Visuals', '', 'AI',
   'Pink, black and green patterned forms move between clothing and the body. Published as Yuzen, the work uses AI imagery to create a cinematic study of surface and gesture. English curatorial title assigned by the Atlas.'),
 'DX9jpYgDOU3': ('Let’s Go!', 'Gizem Akdağ', '', 'AI',
   'A compact, tree-covered landscape appears against a deep teal background. The composition transforms a familiar natural texture into an isolated, improbable world. Instagram identifies the publication as AI content.'),
 'DZ5Gvy2DAy-': ('Alo — Cloud Wave Visuals', 'Gizem Akdağ', '', 'FASHION',
   'A cloud-like form meets a saturated blue wave in visuals created for Alo. Gizem Akdağ combines atmospheric softness and the movement of water. English curatorial title assigned by the Atlas; tools are not disclosed.'),
 'De8m59ZDZIi': ('Second Skin', 'Studio Saint Blaise', '', 'AI',
   'A close study of a scaled creature emphasises metallic sheen, repeated patterns and intricate surface detail. The artist describes the work as an exploration of nature’s hidden opulence and explicitly identifies AI photography.'),
 'DdHKqE8C4_V': ('A Bird in Her Hair', '@yusoncho', '', 'AI',
   'A small bird nestles among flowing strands of hair in a surreal beauty portrait. The publication carries Instagram’s AI-content label. English curatorial title assigned by the Atlas; tools are not specified.'),
 'DYKb8cbDJIx': ('Connection Not Found', 'Katsukokoiso', 'Kling', 'AI',
   'An imagined gathering of figures occupies a precarious, dreamlike architectural space. The artist credits Kling for animation while leaving the image-generation tool unnamed. The work explores disconnection through synthetic visual storytelling.'),
 'DYPoxd2s-Kw': ('Scroll Fever', 'Katsukokoiso', 'Krea K2; Suno', 'AI',
   'A screen-lit figure becomes part of a dark visual reflection on compulsive scrolling. The artist identifies Krea K2 for the imagery and Suno for music, combining synthetic portraiture and a deliberately uneasy atmosphere.'),
 'DdEFX9CAYJA': ('Orchid Life', '@woosuummin', '', 'AI',
   'An orchid and a human figure meet within a pale, softly lit environment. The work explores the relationship between botanical forms, scale and the body. The artist identifies it as an AI creation.'),
 'DSUmZ3AklDu': ('Lotus Life', '@woosuummin', '', 'AI',
   'A figure appears among lotus leaves and pink flowers, merging a familiar human presence with an imagined aquatic setting. The original publication identifies the work as an AI creation without specifying tools.'),
 'Derk57oNgbW': ('Wrong Floor', 'Joann Creative Studio', '', 'AI',
   'A door and an unexpected object transform a familiar corridor into a small surreal encounter. The work belongs to Joann’s imaginary visual practice and carries Instagram’s AI-content label. Production tools are not specified.'),
 'De8fvCFS-DH': ('Flowers on a Studio Floor', 'Jeehyun Kim / ANREAL', '', 'FILM',
   'AI-generated flowers transform the floor throughout a dance film. AI VFX are credited to Jeehyun Kim, with direction by Gabeen Byun, cinematography by Minsu Kim and performance by Kosiia. The work combines filmed performance and synthetic botanical imagery.'),
 'DdtsvvCiWo2': ('JellyCity — Moon Festival', 'Wenhui Lim / Niceaunties', '', 'AI',
   'JellyCity’s timepiece district becomes a setting for a moon-festival greeting. This imagined city belongs to the Auntieverse, which Wenhui Lim identifies as an AI-built world on her official portfolio. English curatorial title assigned by the Atlas.'),
 'Ddq8qOlifRk': ('Still Life, Auntie’s Kitchen', 'Wenhui Lim / Niceaunties', '', 'AI',
   'Generated objects are assembled into a digital collage inspired by a herbarium specimen, family histories and the artist’s lost painting. The work extends the AI-built Auntieverse into compositions printed on handmade paper for an exhibition.'),
}

OFFICIAL_TITLES = {'Deufwm8CACa','DezTQLAmDQ-','De4WDWSjKcv','Deu_bMmhW7L',
 'De7KySARB0c','DZXJGYEgWEz','DdJb0SnNlCE','DbWQDWfiLGr','DX9jpYgDOU3',
 'De8m59ZDZIi','DYKb8cbDJIx','DYPoxd2s-Kw','DdEFX9CAYJA','DSUmZ3AklDu',
 'Derk57oNgbW','Ddq8qOlifRk'}
DESIGN_CONCEPTS = {'De6AoTjG1vk','DZyF1X2knXG','DbWQDWfiLGr'}
BRAND_PROJECTS = {'DYeptCFjRE6','DWWvZAWjavc','DZ5Gvy2DAy-'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    rows=json.loads((BASE/'curation/saved-oct26-selected.json').read_text(encoding='utf-8'))
    videos={row['code']:row for row in json.loads((BASE/'curation/saved-oct26-video-prepared.json').read_text(encoding='utf-8'))}
    if len({row['code'] for row in rows}) != len(rows) or set(EDITORIAL) != {row['code'] for row in rows}:
        raise ValueError('Editorial selections and verified batch must match exactly.')
    prepared=[]
    for row in rows:
        title,artist,tools,category,description=EDITORIAL[row['code']]
        cover=BASE/'media'/row['cover_file']
        with Image.open(cover) as image:
            if min(image.size)<100: raise ValueError('Cover too small')
            image.verify()
        if row['username']=='blumquist_' or row['requested_code'] != row['code']:
            raise ValueError('Rejected creator or mismatched canonical post')
        media_format='video' if row['source_is_video'] else 'image'
        if row['code']=='DU1F6bajIbv': media_format='series'
        if category=='AI' and media_format=='video': category='FILM'
        disclosure=row['ai_disclosure'][:100]
        metadata=dict(title=title,artist=artist,tools=tools,category=category,
            description=description,instagram_shortcode=row['code'],instagram_username=row['username'],
            source_url=row['url'],image=row['cover'],cover_file=row['cover_file'],
            published_at=datetime.fromisoformat(row['published_on']).replace(tzinfo=timezone.utc),
            year=int(row['published_on'][:4]),media_format=media_format,
            project_type='brand' if row['code'] in BRAND_PROJECTS else 'experiment' if row['code'] in DESIGN_CONCEPTS else 'art',
            creative_field='fashion' if category=='FASHION' else 'design' if category=='DESIGN' else 'film' if category=='FILM' else 'art',
            title_is_editorial=row['code'] not in OFFICIAL_TITLES,ai_disclosure=disclosure,
            media_items=[dict(kind='image',url=settings.MEDIA_URL+row['cover_file'],is_cover=True,
                             original_url=row['cover'])])
        if row['source_is_video']:
            video=videos[row['code']]
            for key in ('preview_file','playback_file'):
                if not (BASE/'media'/video[key]).is_file():
                    raise ValueError(f'Missing prepared video for {row["code"]}')
            metadata['media_items'].append(dict(kind='video',
                url=settings.MEDIA_URL+video['playback_file'],
                original_url=video['original_url'],
                preview_url=settings.MEDIA_URL+video['preview_file'],
                playback_url=settings.MEDIA_URL+video['playback_file'],preview_width=320))
        preview=Project(**metadata)
        preview.full_clean(validate_unique=False)
        prepared.append((row,metadata,hashlib.sha256(cover.read_bytes()).hexdigest()))
    (BASE/'curation/saved-oct26-reviewed-en.json').write_text(json.dumps([
        dict(url=row['url'],summary=meta['title'],artist_credit=meta['artist'],category=meta['category'],
             description=meta['description'],tools=meta['tools'],ai_disclosure=meta['ai_disclosure'])
        for row,meta,_ in prepared],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not args.apply:
        print(f'{len(prepared)} validated works ready; no projects published.')
        return
    output=BASE.parent/'outputs/01a17412-curation'
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    with sqlite3.connect(settings.DATABASES['default']['NAME']) as source:
        with sqlite3.connect(output/f'before-saved-oct26-{stamp}.sqlite3') as destination:
            source.backup(destination)
    report=[]
    with transaction.atomic():
        for row,metadata,digest in prepared:
            project,created=Project.objects.get_or_create(instagram_shortcode=row['code'],defaults=metadata)
            if not created:
                report.append(dict(code=row['code'],id=project.pk,status='already existed; unchanged'))
                continue
            if not project.dominant_color:
                raise ValueError(f'Colour classification missing for {project.pk}')
            submission,_=CurationSubmission.objects.get_or_create(source_key=f'instagram:{row["code"]}',defaults={
                'source_url':row['url'],'media_type':'reel' if '/reel/' in row['url'] else 'post',
                'publisher':row['username'],'published_on':row['published_on'],
                'title':project.title,'suggested_title':project.title,'artist':project.artist,
                'category':project.category,'project_year':project.year,'tools':project.tools,
                'description':project.description,'ai_confirmed':True,
                'notes':f'AI evidence: {row["ai_evidence"]}\n{row["ai_disclosure"]}\nSource checked 2026-10-26. User requested confirmed AI only. Public cover cached.' + (' First video cached with a lightweight preview and local playback.' if row['source_is_video'] else '')})
            submission.project=project
            submission.status='published'
            submission.save(update_fields=['project','status'])
            report.append(dict(id=project.pk,code=row['code'],title=project.title,artist=project.artist,
                source_url=project.source_url,supplied=row['supplied'],ai_evidence=row['ai_evidence'],
                color=project.dominant_color,format=project.media_format,cover_sha256=digest,
                local_video=row['source_is_video'],status='created'))
    (BASE/'curation/saved-oct26-import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{sum(row["status"]=="created" for row in report)} created; {Project.objects.count()} projects in the Atlas.')

if __name__=='__main__':
    main()
