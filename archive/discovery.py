"""Shared discovery labels, with optional curator overrides."""
import re


from .classification import project_type, media_format, creative_field


_CREATOR_ALIASES = {
    '@priscila.nassar': 'Priscila Nassar', '@priscilanassar': 'Priscila Nassar',
    '@prina.lab': 'Prina Lab', '@dazzle.ai': 'Dazzle AI',
    '@buddhastears_': 'Mauricio Orozco',
    'Jeferson Araujo Studio': 'Jeferson Araujo',
    'Bruna Bismara / Touch of Oddity': 'Bruna Bismara (Touch of Oddity)',
    'Infrarouge / Anthony Tournadre': 'Anthony Tournadre (Infrarouge)',
    'Veronika Pell / Mindeye': 'Veronika Pell (Mindeye)',
    'The Acid Times / Bruno Zampoli': 'Bruno Zampoli (The Acid Times)',
    'Jeehyun Kim / ANREAL': 'Jeehyun Kim (ANREAL)',
    'Wenhui Lim / Niceaunties': 'Wenhui Lim (Niceaunties)',
}
_CREATOR_ALIASES = {key.casefold(): value for key, value in _CREATOR_ALIASES.items()}


def canonical_creator(name):
    name = re.sub(r'\s+', ' ', name).strip()
    return _CREATOR_ALIASES.get(name.casefold(), name)


def creator_names(project):
    credit = re.split(r',\s*published by\b', project.artist, flags=re.I)[0]
    credit = re.sub(r'\s*\(@[^)]+\)', '', credit).strip()
    if credit.casefold() in _CREATOR_ALIASES:
        return (canonical_creator(credit),)
    names = [canonical_creator(name) for name in re.split(r'\s+(?:/|&|\+|and)\s+', credit, flags=re.I) if name.strip()]
    return tuple(dict.fromkeys(names))


_TOOL_NAMES = ('Midjourney','Runway','Krea','Dreamina','Seedance','Nano Banana',
               'Kling','MiniMax','OpenArt','Higgsfield','Soul','Artlist','Claude',
               'Flora','InVideo','CapCut')


def tool_names(value):
    names = []
    for item in re.split(r'[,;\n]+', value):
        item = item.strip()
        if not item:
            continue
        recognised = [name for name in _TOOL_NAMES if re.search(r'\b'+re.escape(name)+r'\b',item,re.I)]
        names.extend(recognised or [item])
    return tuple(dict.fromkeys(names))
