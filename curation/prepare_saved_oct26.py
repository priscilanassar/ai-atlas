"""Prepare only verified AI works from the user's saved-post references."""
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rows = json.loads((ROOT / 'saved-oct26-post-research.json').read_text(encoding='utf-8'))
existing = json.loads((ROOT / 'saved-oct26-existing.json').read_text(encoding='utf-8'))
existing_codes = {row['instagram_shortcode'] for row in existing if row['instagram_shortcode']}
known_published = set()
for path in ROOT.glob('*-reviewed-en.json'):
    if path.name.startswith('saved-oct26'):
        continue
    for item in json.loads(path.read_text(encoding='utf-8')):
        code = item.get('url', '').rstrip('/').split('/')[-1]
        if code:
            known_published.add(code)

EXTERNAL = {
    'DdtsvvCiWo2': 'https://www.niceaunties.com/',
    'Ddq8qOlifRk': 'https://www.niceaunties.com/',
}
CONFIRMED = {
    'Dcv5WIxMBan', 'Det7Fs6RlC-', 'Deufwm8CACa', 'DePPoA1mPSN',
    'DezTQLAmDQ-', 'De6AoTjG1vk', 'Ddt5Mt0BmUi', 'De4WDWSjKcv',
    'DaMp5EnDBJs', 'DYeptCFjRE6', 'DWWvZAWjavc', 'Deu_bMmhW7L',
    'De7KySARB0c', 'DZXJGYEgWEz',
    'DdPQWeoMW6h', 'Dc_PaJ3slfq', 'DclzvsvjJkp', 'DU1F6bajIbv',
    'Dc5x8-HNuSV', 'DdJb0SnNlCE', 'DZyF1X2knXG', 'DbWQDWfiLGr',
    'Dd4MatXO_tk', 'DX9jpYgDOU3', 'DZ5Gvy2DAy-', 'De8m59ZDZIi',
    'DdHKqE8C4_V', 'DYKb8cbDJIx', 'DYPoxd2s-Kw', 'DdEFX9CAYJA',
    'DSUmZ3AklDu', 'Derk57oNgbW', 'De8fvCFS-DH',
    *EXTERNAL,
}
# Workshop announcements are research references, not artwork entries.
EXCLUDE_REASONS = {
    'DeyuCweDSO5': 'Physical sculpture; no AI involvement documented.',
    'DeUb-yfMBRw': 'Blender, VFX and point-cloud workflow disclosed; no AI evidence.',
    'Dc1FaMjNDEI': 'Creative coding and generative art disclosed; no AI evidence.',
    'DKMoSS2MWiU': 'CGI campaign; no AI evidence.',
    'DDJnIX1v0hu': 'CGI/VFX production and practical materials disclosed; no AI evidence.',
    'DeJJTigzHAO': 'Real-time glitch camera effects; no AI evidence.',
    'DejxTcltRBX': 'Music and sound experiment; no AI evidence.',
}

selected, audit = [], []
for row in rows:
    row.pop('excerpt', None)  # Do not retain unrelated public comments.
    meta = {item['key']: item['value'] for item in row['meta']}
    url = meta.get('og:url', '')
    code = url.rstrip('/').split('/')[-1]
    caption_meta = meta.get('og:description', '')
    match = re.search(r' - ([\w.]+) no (\w+ \d+, \d{4}): "(.*)"\.\s*$', caption_meta, re.S)
    if not match:
        # Some publishers hide the like count.
        match = re.search(r'^([\w.]+) no (\w+ \d+, \d{4}): "(.*)"\.\s*$', caption_meta, re.S)
    if not match:
        raise ValueError(f'No publisher/date/caption for {row["code"]}')
    username, day, caption = match.groups()
    if username == 'blumquist_':
        raise ValueError('Creator rejected by user')
    reason = ''
    if row['code'] != code:
        reason = 'Requested URL resolves to a different canonical publication; held for review.'
    elif code in existing_codes:
        reason = 'Already in the catalogue; left unchanged.'
    elif code in known_published and not row['supplied']:
        reason = 'Previously curated batch; not restored automatically.'
    elif code not in CONFIRMED:
        reason = EXCLUDE_REASONS.get(code, 'No project-specific AI evidence found; not published.')
    evidence = EXTERNAL.get(code) or url
    disclosure = ('Artist identifies the Auntieverse as an AI-built world on the official portfolio.'
                  if code in EXTERNAL else
                  'Instagram identifies this publication as AI content.' if row['aiLabel'] else
                  'AI involvement or generative tools explicitly disclosed in the source caption.')
    item = dict(code=code, requested_code=row['code'], url=url, username=username,
                published_on=datetime.strptime(day, '%B %d, %Y').date().isoformat(),
                caption=caption, ai_label=row['aiLabel'], ai_evidence=evidence,
                ai_disclosure=disclosure, supplied=row['supplied'], reason=reason)
    audit.append(item)
    if not reason:
        image = meta['og:image']
        item['cover'] = image
        item['source_is_video'] = bool(row['videos']) or '/reel/' in url
        selected.append(item)

(ROOT / 'saved-oct26-post-research.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(ROOT / 'saved-oct26-selected.json').write_text(json.dumps(selected, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(ROOT / 'saved-oct26-screening.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(f'{len(selected)} verified new works; {sum(row["supplied"] for row in selected)} supplied and {sum(not row["supplied"] for row in selected)} related.')
print('Unpublished supplied references:', [(row['requested_code'],row['reason']) for row in audit if row['supplied'] and row['reason']])
