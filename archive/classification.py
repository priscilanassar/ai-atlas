"""Local classification rules. No API, network request or AI-authenticity inference."""
import json
import re
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def rules():
    # Packaged alongside Python code; restart/redeploy after editing the rules.
    return json.loads(Path(__file__).with_name('classification_rules.json').read_text(encoding='utf-8'))


def project_type(project):
    if project.project_type:
        return project.project_type
    config = rules()['project_type']
    text = f'{project.title} {project.description}'
    for rule in config['rules']:
        if re.search(rule['pattern'], text, re.I):
            return rule['value']
    return config['default']


def creative_field(project):
    if project.creative_field:
        return project.creative_field
    config = rules()['creative_field']
    for rule in config['title_rules']:
        if (not rule.get('category') or project.category == rule['category']) and re.search(rule['pattern'], project.title, re.I):
            return rule['value']
    return config['category_map'].get(project.category, config['default'])


def media_format(project):
    if project.media_format:
        return project.media_format
    config = rules()['media_format']
    media = [item for item in project.media_items if isinstance(item, dict) and not item.get('is_cover')]
    if len(media) > 1:
        return 'series'
    if any(item.get('kind') == 'video' for item in media) or '/reel/' in project.source_url or project.category in config['video_categories']:
        return 'video'
    if re.search(config['series_pattern'], f'{project.title} {project.description}', re.I):
        return 'series'
    return config['default']


def describe(project):
    """Public metadata plus provenance, suitable for admin review and JSON reports."""
    values = {'project_type': project_type(project), 'creative_field': creative_field(project), 'media_format': media_format(project)}
    return {field: {'value': value, 'source': 'curator' if getattr(project, field) else 'automatic rule'}
            for field, value in values.items()}
