
from django.shortcuts import render
from archive.models import Project
from collection.models import Collection
from collection.forms import CollectionForm
from datetime import date
from archive.views import can_delete_projects
from .globe_layout import build_globe_tiles
from archive import discovery

def home(request):
    sort_choices = [('date_desc', 'Project date: newest'), ('date_asc', 'Project date: oldest'),
                    ('name_asc', 'Name: A–Z'), ('name_desc', 'Name: Z–A'), ('color', 'Color palette')]
    sort = request.GET.get('sort', 'date_desc')
    if sort not in dict(sort_choices):
        sort = 'date_desc'
    color = request.GET.get('color', '')
    if color not in dict(Project.COLOR_CHOICES) and color != 'unassigned':
        color = ''
    catalogue = list(Project.objects.defer('instagram_caption', 'country_evidence', 'ai_disclosure'))
    indexed = [(project, {
        'type': discovery.project_type(project),
        'format': discovery.media_format(project),
        'field': discovery.creative_field(project),
        'creators': {name.casefold(): name for name in discovery.creator_names(project)},
        'tools': {name.casefold(): name for name in discovery.tool_names(project.tools)},
    }) for project in catalogue]
    creator_labels = {key: label for _, metadata in indexed for key, label in metadata['creators'].items()}
    countries = {project.country.strip().casefold(): project.country.strip() for project in catalogue if project.country.strip()}
    tool_labels = {key: label for _, metadata in indexed for key, label in metadata['tools'].items()}
    def choice(name, allowed):
        value = request.GET.get(name, '').strip().casefold()
        return value if value in allowed else ''
    selected_type = choice('type', dict(Project.PROJECT_TYPE_CHOICES))
    selected_format = choice('format', dict(Project.FORMAT_CHOICES))
    selected_field = choice('field', dict(Project.CREATIVE_FIELD_CHOICES))
    creator_query = discovery.canonical_creator(request.GET.get('creator', '')).casefold()
    selected_creator = creator_query if creator_query in creator_labels else ''
    selected_country = choice('country', set(countries) | {'undocumented'})
    selected_tool = choice('tool', set(tool_labels) | {'undisclosed'})
    search = request.GET.get('q', '').strip()[:200]
    projects = [project for project, metadata in indexed
                if (not search or search.casefold() in project.title.casefold())
                and (not color or project.dominant_color == ('' if color == 'unassigned' else color))
                and (not selected_type or metadata['type'] == selected_type)
                and (not selected_format or metadata['format'] == selected_format)
                and (not selected_field or metadata['field'] == selected_field)
                and (not selected_creator or selected_creator in metadata['creators'])
                and (not selected_country or (not project.country.strip() if selected_country == 'undocumented'
                                              else project.country.strip().casefold() == selected_country))
                and (not selected_tool or (not metadata['tools'] if selected_tool == 'undisclosed'
                                          else selected_tool in metadata['tools']))]
    if sort.startswith('name'):
        key = lambda project: (project.title.casefold(), project.pk)
    elif sort == 'color':
        palette = dict((value, index) for index, (value, _) in enumerate(Project.COLOR_CHOICES))
        key = lambda project: (palette.get(project.dominant_color, len(palette)), project.title.casefold(), project.pk)
    else:
        key = lambda project: (project.project_date or (project.published_at.date() if project.published_at else date(max(1, min(9999, project.year)), 1, 1)), project.pk)
    projects.sort(key=key, reverse=sort in ('name_desc', 'date_desc'))
    matching_count = len(projects)
    projects = projects[:1200]
    tiles = build_globe_tiles(projects)
    map_data = {str(project.pk): {
        'color': project.dominant_color or 'unassigned',
        'country': project.country.strip() or 'Not documented',
        'type': dict(Project.PROJECT_TYPE_CHOICES)[discovery.project_type(project)],
        'format': dict(Project.FORMAT_CHOICES)[discovery.media_format(project)],
        'field': dict(Project.CREATIVE_FIELD_CHOICES)[discovery.creative_field(project)],
        'year': str((project.project_date or project.published_at).year if (project.project_date or project.published_at) else project.year),
    } for project in projects}
    return render(request, 'index.html', {
        'tiles': tiles, 'project_count': matching_count,
        'map_data': map_data, 'country': selected_country,
        'country_choices': sorted(countries.items(), key=lambda row: row[1]),
        'can_delete_projects': can_delete_projects(request.user),
        'sort': sort, 'sort_choices': sort_choices, 'color': color,
        'color_choices': Project.COLOR_CHOICES,
        'search': search,
        'project_type': selected_type, 'media_format': selected_format,
        'creative_field': selected_field, 'creator': selected_creator, 'tool': selected_tool,
        'project_type_choices': Project.PROJECT_TYPE_CHOICES,
        'format_choices': Project.FORMAT_CHOICES,
        'creative_field_choices': Project.CREATIVE_FIELD_CHOICES,
        'creator_choices': sorted(creator_labels.items(), key=lambda row: row[1].casefold()),
        'tool_choices': sorted(tool_labels.items(), key=lambda row: row[1].casefold()),
        'has_filters': bool(search or color or selected_type or selected_format or selected_field
                            or selected_creator or selected_tool or selected_country or sort != 'date_desc'),
        'collections': Collection.objects.filter(owner=request.user) if request.user.is_authenticated else [],
        'collection_form': CollectionForm(),
    })
