from collections import Counter
from django.core.management.base import BaseCommand
from archive.models import Project
from archive.colors import detect_color


class Command(BaseCommand):
    help = 'Classify locally stored project covers. Existing editorial colors are preserved unless --force is passed.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true')

    def handle(self, force=False, **options):
        projects = Project.objects.exclude(cover_file='')
        if not force:
            projects = projects.filter(dominant_color='')
        counts = Counter()
        for project in projects:
            try:
                with project.cover_file.open('rb') as cover:
                    color = detect_color(cover)
            except (OSError, ValueError) as error:
                self.stderr.write(f'{project.pk}: could not classify cover ({error})')
                continue
            Project.objects.filter(pk=project.pk).update(dominant_color=color)
            counts[color] += 1
        self.stdout.write(self.style.SUCCESS(f'{sum(counts.values())} covers classified: {dict(counts)}'))
