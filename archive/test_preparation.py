from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PIL import Image
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from .classification import describe, rules
from .models import Project


def cover(name, rgb):
    buffer = BytesIO()
    Image.new('RGB', (1200, 800), rgb).save(buffer, 'PNG')
    return ContentFile(buffer.getvalue(), name=name)


class PreparationTests(TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.settings = override_settings(MEDIA_ROOT=self.folder.name)
        self.settings.enable()
        self.addCleanup(self.settings.disable)

    def test_save_creates_small_cover_without_replacing_original_or_manual_labels(self):
        project = Project.objects.create(title='Architecture Campaign', artist='Artist', category='AI',
            cover_file=cover('blue.png', (20, 80, 240)), project_type='art', creative_field='abstract', dominant_color='red')
        project.refresh_from_db()
        self.assertEqual(project.dominant_color, 'red')
        self.assertEqual(describe(project)['project_type'], {'value': 'art', 'source': 'curator'})
        with Image.open(project.thumbnail_file.path) as image:
            self.assertEqual(image.format, 'WEBP')
            self.assertLessEqual(max(image.size), 320)
        with Image.open(project.cover_file.path) as image:
            self.assertEqual(image.size, (1200, 800))
        self.assertContains(self.client.get(reverse('home')), project.thumbnail_url)
        self.assertContains(self.client.get(reverse('project_detail', args=[project.pk])), project.cover_url)

    def test_new_cover_refreshes_thumbnail_and_unchanged_cover_is_not_processed(self):
        project = Project.objects.create(title='Blue', artist='Artist', category='AI', cover_file=cover('blue.png', (20, 80, 240)))
        old = project.thumbnail_url
        with patch('archive.thumbnails.Image.open', side_effect=AssertionError('Unchanged cover decoded')):
            project.title = 'Renamed'
            project.save()
        project.cover_file = cover('green.png', (20, 190, 40))
        project.dominant_color = ''
        project.save()
        project.refresh_from_db()
        self.assertNotEqual(project.thumbnail_url, old)
        self.assertEqual(project.dominant_color, 'green')

    def test_remote_url_has_safe_fallback_and_rules_update_from_metadata(self):
        project = Project.objects.create(title='Portrait', artist='Artist', category='AI', image='https://example.org/art.jpg')
        self.assertEqual(project.thumbnail_url, project.image)
        self.assertEqual(project.dominant_color, '')
        self.assertEqual(describe(project)['project_type']['value'], 'art')
        project.description = 'Independent experiment'
        project.media_items = [{'kind': 'video', 'url': '/media/film.mp4'}]
        project.save()
        project.refresh_from_db()
        self.assertEqual(describe(project)['project_type']['value'], 'experiment')
        self.assertEqual(describe(project)['media_format']['value'], 'video')
        self.assertEqual(project.project_type, '')
        self.assertEqual(project.country, '')
        self.assertEqual(project.ai_disclosure, '')

    def test_batch_is_idempotent_and_dry_run_does_not_change_files_or_data(self):
        project = Project.objects.create(title='Study', artist='Artist', category='AI', cover_file=cover('cover.png', (240, 10, 10)))
        Project.objects.filter(pk=project.pk).update(thumbnail_file='', thumbnail_source='')
        files = sorted(Path(self.folder.name).rglob('*'))
        call_command('prepare_atlas', dry_run=True, stdout=StringIO())
        project.refresh_from_db()
        self.assertFalse(project.thumbnail_file)
        self.assertEqual(files, sorted(Path(self.folder.name).rglob('*')))
        call_command('prepare_atlas', stdout=StringIO())
        project.refresh_from_db()
        self.assertTrue(project.thumbnail_file)
        output = StringIO()
        call_command('prepare_atlas', stdout=output)
        self.assertIn('0 thumbnails generated', output.getvalue())

    def test_json_rules_only_return_supported_categories(self):
        config = rules()
        for key, choices in [('project_type', Project.PROJECT_TYPE_CHOICES), ('creative_field', Project.CREATIVE_FIELD_CHOICES)]:
            allowed = dict(choices)
            self.assertIn(config[key]['default'], allowed)
            for rule in config[key].get('rules', config[key].get('title_rules', [])):
                self.assertIn(rule['value'], allowed)
        self.assertTrue(set(config['creative_field']['category_map'].values()) <= set(dict(Project.CREATIVE_FIELD_CHOICES)))
