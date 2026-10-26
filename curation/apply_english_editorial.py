"""Run with manage.py shell to apply reviewed English editorial copy.

Original captions remain available in the admin and through source links.
"""
import json
from pathlib import Path
from django.db import transaction
from archive.models import Project

COPY = {
    'DWJq4mFjFHF': ('Big Bags Are Back', 'A fashion campaign and pop-up announcement by Break Archive, centred on oversized bags. The source does not identify the production as AI-generated.'),
    'DYztia1N0F1': ('Strange Encounters', 'An experimental visual reel by Special Benedict. The source caption consists of symbols and does not specify the production tools.'),
    'DaCuOljmZoK': ('Flowers in Every Direction', 'A floral origami study by Nvmhyuk, exploring flowers and folded forms. AI use is not specified in the source caption.'),
    'DKa00eQqJOB': ('Love You', 'A digital-art film by Holymariia exploring affection and transformation. The source labels it digital art without specifying an AI workflow.'),
    'DPc8vyvCNIM': ('Just Look into My Eyes', 'A digital-art reel by Holymariia built around the invitation to look into the subject’s eyes. Production tools are not specified in the caption.'),
    'DYhrI8QjfC8': ('A World Unfastened', 'An experimental image series by Special Benedict. The artist’s original post is linked for the complete carousel and source context.'),
    'DV95_eWDDQP': ('A Geometric Reverie', 'An experimental visual study published by Mauricio Orozco. The original caption does not identify the work’s title or tools.'),
    'Dba97RAnMDf': ('Bathing in Another World', 'An experimental bath-themed visual study by Mauricio Orozco. This is a curatorial title; the source caption does not specify the technique.'),
    'DZIMkh_Ec-V': ('An Unexpected Vogue Editorial', 'An editorial image published by Blobby Bloherty with credits to Vogue, writer Tamar Adler and an editor. The caption does not specify an AI workflow.'),
    'DWOs1UYDLRi': ('Jacquemus — The Adaptive Chameleon', 'An independent concept by Eliza Sofia in which a chameleon changes colour while moving across a Jacquemus bag. The publisher describes an AI-led production. Not affiliated with Jacquemus.'),
    'DLC_AyLRYuI': ('The Soft Exit: Discomfort in Disguise', 'A generative fashion editorial by Novosyna exploring discomfort beneath a soft visual surface. The source credits generative AI and Midjourney.'),
    'DQeTcjDjZY8': ('When the World Trembles, She Does Not', 'A generative editorial by Novosyna exploring composure and resilience. The artist identifies the imagery as AI-generated.'),
    'DXq3YMWjb4R': ('Desigual — Imaginary Behind the Scenes', 'AI-generated social content for Desigual, built around a fictional behind-the-scenes concept.'),
    'DUbSMudjXSE': ('Fendi — An Imaginary Ride, Study II', 'An independent Fendi-inspired concept film made with Nano Banana 2, Kling 2.6 and InVideo. The artist explicitly states that it is fictional and not affiliated with Fendi.'),
    'DUYo8DRDUD3': ('Fendi — An Imaginary Ride, Study I', 'An independent Fendi-inspired concept using generated base frames and AI animation. Tools credited by the creator include Nano Banana 2, Kling 2.6 and InVideo.'),
    'DWonlKxlRrA': ('Portraits from Alternate Universes', 'A series of imagined alternate identities by Daisy Pyo. The caption credits Soul 2.0 as the tool used to create the work.'),
    'DdXMjl_S577': ('Chanel — An AI Visual Transformation', 'A visual project by Papodipokas featuring Afroboneca. The artist describes AI-generated imagery, animation, direction and editing developed from reference photographs.'),
    'DZNWNW1MT32': ('Sauer — Impossible Flora', 'A botanical jewellery concept published as Impossible Flora: A Cabinet of Botanies for Sauer. The source identifies the project but does not explicitly describe its AI process.'),
    'DZaA-nkFuPZ': ('Bodies Beyond This World', 'An experimental body study by Papodipokas, imagining how different physical realities could reshape the human form. The source caption does not specify the production technique.'),
    'DYQHdw7Ihjh': ('Blooming Diamonds', 'A visual exploration of flowers and jewellery published by Juliana Frug. The caption names the work but does not identify the production tools.'),
    'DV8ixOPADMA': ('Blacko — The Unstoppable Cat', 'A character portrait of Jack Black, also called Blacko, published by Juliana Frug. The caption describes the character without confirming an AI technique.'),
    'DbwPdcMJOde': ('Have You Been Here Before?', 'A dreamcore video exploring the strange familiarity of imagined places. Otávio Pompeu credits Seedance 2.5 and CapCut.'),
    'DVbgKFeFf-i': ('Santa Lolla — Return to Essentials', 'AI interventions for Santa Lolla’s Return to Essentials collection. The published credits name Priscila Nassar, Erotidesnai and Data Dialogues among the collaborators.'),
    'Dd9u4Luofe_': ('FARM ETC and Lev — A Generative Journey', 'A film created by Priscila Nassar for FARM ETC and Lev Bicycles. The artist credits Claude, Seedance 2.5 and Minimax H3.'),
    'DaxSsoMNlXg': ('Zara Beauty — An AI Creative Concept', 'AI social content and creative concept development for Zara Beauty, with AI production credited to Maria Homs.'),
    'DXXNvxXDQB1': ('YOYOYO — Play Reimagined', 'A collaboration between PORTO ROCHA and Google DeepMind using Nano Banana Pro to develop a brand and a realised 3D product concept.'),
    'DZTiIuixiXL': ('A Quiet Business in the Backrooms', 'A surreal commercial-space video by Tnayha using the visual language of the backrooms. The caption does not identify an AI tool.'),
    'DezVjPKoHgf': ('Inanimate Objects — Hairdryer', 'The third instalment of Juliana Frug’s series imagining life as an inanimate object. The artist credits Seedance 2.5 and CapCut.'),
    'DeewvyRoKjf': ('Folders, Prompts and Therapy', 'A surreal short film by Juliana Frug, playing with the difference between a prompt and its result. Made with Seedance 2.5 in CapCut.'),
    'DW7LHPYj4dJ': ('Through the Wallpaper', 'A generative video experiment that makes a hand appear to interact with a computer wallpaper. The creator documents a Dreamina Seedance 2.0 and CapCut workflow.'),
    'DVTp4oGjgky': ('Power Rangers — A Generative Reimagining', 'An independent reinterpretation of a classic television opening, created with NanoBanana imagery and Seedance 2.0 animation.'),
    'DZacB6KjSsz': ('By My Side, Until the End', 'An AI-generated editorial by Novosyna reflecting on companionship and attachment.'),
    'DZStS2uDdcF': ('The Path to Rest', 'A generative editorial by Novosyna exploring rest, memory and connection.'),
    'DZNBhFdja5Z': ('Sisterhood Souls', 'A generative image series by Novosyna centred on togetherness and shared identity.'),
    'DY7b4B5DR8i': ('Return to You', 'An AI-generated editorial by Novosyna about returning to a place of belonging.'),
    'DUomzb5DXln': ('Returning to an Imagined World', 'A return to Novosyna’s generative visual universe, with AI creation explicitly acknowledged in the caption.'),
    'DQW92x2jdhi': ('Sleeping Between Worlds', 'An AI-generated editorial by Novosyna exploring the space between rest and imagination. The source credits Midjourney among its creative references.'),
    'DdEK_WfkTDn': ('Ipanema — Real Products, Imagined Worlds', 'A footwear campaign combining AI-generated images with realistic sandal integration. The credits name Juliana Frug, Priscila Nassar, Feito AI and retouching collaborators.'),
    'DYaCpFfDZhO': ('H&M — An Imagined Summer', 'AI-generated campaign content for H&M’s summer collection, published by Dazzle AI.'),
    'DYb1kWDNGNY': ('Amiri — MA-94 in Motion', 'AI-generated content for the Amiri MA-94 sneakers, with AI production credited to Maria Homs.'),
    'DewyPnsjX0Y': ('Zalando — A Generative Christmas', 'Christmas campaign content for Zalando, created through AI production and creative direction by Maria Homs.'),
    'DerkoXSDVDf': ('Mechanical Motion', 'A robotic fashion experiment that the publisher explicitly identifies as entirely AI-generated.'),
    'DemU66Vjedg': ('Can You Spot the AI?', 'A casting and image-generation study inviting the viewer to distinguish synthetic imagery. The source discusses the prompts used to create the work.'),
    'DejsKc_DBdM': ('Zara — A Generative Fashion Story', 'AI-generated fashion content for Zara, published by Dazzle AI and credited to Maria Homs.'),
    'DX4kB4BjKsL': ('Real Products, Imagined Campaigns', 'A product-integration study by Beatrice von Winterfeldt, combining real product imagery with AI-generated campaign environments. Presented as an independent concept.'),
    'DXyi23kDu8d': ('Luxury Beyond the Studio', 'AI-generated luxury imagery by Beatrice von Winterfeldt, integrating real products into imagined settings without a physical shoot.'),
    'Ddl_KXYI-fL': ('Breuninger — Autumn and Winter Beauty', 'AI-generated imagery and motion for Breuninger’s 2026 autumn/winter beauty campaign. The credits identify Beatrice von Winterfeldt and Desyre AI.'),
}

with transaction.atomic():
    for shortcode, (title, description) in COPY.items():
        Project.objects.filter(instagram_shortcode=shortcode).update(title=title, description=description, title_is_editorial=True)
    Project.objects.filter(instagram_shortcode__isnull=True, title='Santa Lolla').update(
        title='Santa Lolla — A Creative Collaboration',
        description='A fashion and visual-direction project by Orbis Nucleo and Prina Lab.')

print(f'Applied English editorial copy for {len(COPY)} imported projects.')
