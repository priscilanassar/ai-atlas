import json
from pathlib import Path
from django.core.management.base import BaseCommand
from archive.classification import describe
from archive.colors import detect_color
from archive.models import Project
from archive.thumbnails import prepare_thumbnail


class Command(BaseCommand):
    help = 'Prepare local covers and report automatic labels. Preserves manual labels, original media and existing colors. Does not publish or confirm AI use.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--force-thumbnails', action='store_true')
        parser.add_argument('--report', type=Path)

    def handle(self, **options):
        rows, thumbnails, colors, errors = [], 0, 0, 0
        for project in Project.objects.order_by('pk').iterator(chunk_size=100):
            row = {'id': project.pk, 'title': project.title, 'classification': describe(project),
                   'color': project.dominant_color or 'unassigned'}
            if not options['dry_run'] and project.cover_file:
                updates = {}
                try:
                    if not project.dominant_color:
                        with project.cover_file.open('rb') as source:
                            updates['dominant_color'] = detect_color(source)
                        row['color'] = updates['dominant_color']
                        colors += 1
                    if prepare_thumbnail(project, force=options['force_thumbnails']):
                        updates.update(thumbnail_file=project.thumbnail_file.name, thumbnail_source=project.thumbnail_source)
                        thumbnails += 1
                    if updates:
                        Project.objects.filter(pk=project.pk).update(**updates)
                except (OSError, ValueError) as error:
                    row['error'] = str(error)
                    errors += 1
                    self.stderr.write(f'Project {project.pk}: {error}')
            row['thumbnail_ready'] = bool(project.thumbnail_file and project.thumbnail_source == project.cover_file.name)
            rows.append(row)
        report = {'dry_run': options['dry_run'], 'projects': len(rows), 'thumbnails_generated': thumbnails,
                  'colors_assigned': colors, 'errors': errors, 'items': rows}
        if options['report']:
            options['report'].parent.mkdir(parents=True, exist_ok=True)
            options['report'].write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        self.stdout.write(f'{len(rows)} projects; {thumbnails} thumbnails generated; {colors} missing colors assigned; {errors} errors. Dry run: {options["dry_run"]}.')
