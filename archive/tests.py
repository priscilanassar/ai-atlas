import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase
from django.urls import reverse

from .models import Project, CurationSubmission


class CurationImportTests(TestCase):
    def run_import(self, rows):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'batch.json'
            path.write_text(json.dumps(rows), encoding='utf-8')
            call_command('import_curation', path, stdout=StringIO())

    def test_import_is_idempotent_and_never_publishes(self):
        row = {'source_url': 'https://www.instagram.com/p/ABC123/?img_index=3',
               'publisher': 'artist', 'title': 'Caption title', 'published_on': '2026-05-01'}
        self.run_import([row])
        item = CurationSubmission.objects.get()
        item.notes = 'Reviewer work must survive reimport'
        item.save()
        self.run_import([dict(row, source_url='https://www.instagram.com/artist/reel/ABC123/')])
        self.assertEqual(CurationSubmission.objects.count(), 1)
        self.assertFalse(Project.objects.exists())
        item.refresh_from_db()
        self.assertEqual(item.source_key, 'instagram:ABC123')
        self.assertEqual(item.notes, 'Reviewer work must survive reimport')
        self.assertEqual(item.title, '')
        self.assertIsNone(item.project_year)

    def test_invalid_batch_does_not_partially_import(self):
        with self.assertRaises(CommandError):
            self.run_import([{'source_url': 'https://www.instagram.com/p/ABC123/'},
                             {'source_url': 'https://example.com/p/ABC/'}])
        self.assertFalse(CurationSubmission.objects.exists())

    def test_reviewed_publication_preserves_source_and_does_not_duplicate(self):
        admin = get_user_model().objects.create_superuser('reviewer', password='test-password')
        self.client.force_login(admin)
        complete = CurationSubmission.objects.create(
            source_key='instagram:ABC123', source_url='https://www.instagram.com/p/ABC123/',
            media_type='post', title='Reviewed project', artist='Verified artist',
            category='AI', project_year=2025, ai_confirmed=True)
        incomplete = CurationSubmission.objects.create(
            source_key='instagram:DEF456', source_url='https://www.instagram.com/p/DEF456/', media_type='post')
        url = reverse('admin:archive_curationsubmission_changelist')
        self.assertEqual(self.client.get(url).status_code, 200)
        data = {'action': 'publish_reviewed', '_selected_action': [complete.pk, incomplete.pk]}
        self.client.post(url, data)
        self.client.post(url, data)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.get().source_url, complete.source_url)
        incomplete.refresh_from_db()
        self.assertEqual(incomplete.status, 'pending')
        self.assertFalse(incomplete.project_id)


class ScraperProjectTests(TestCase):
    def test_public_detail_uses_english_copy_not_original_caption(self):
        project = Project.objects.create(
            title='An Imagined Garden', artist='Artist', category='AI',
            description='An English editorial description.',
            instagram_caption='Legenda original em português que deve ficar no admin.')
        response = self.client.get(reverse('project_detail', args=[project.pk]))
        self.assertContains(response, 'An English editorial description.')
        self.assertNotContains(response, 'Legenda original')

    def test_scraper_import_and_separate_detail_page(self):
        record = {
            'url': 'https://www.instagram.com/reel/ABC123/', 'user_posted': 'studio',
            'description': 'A project description with <script>alert(1)</script>',
            'date_posted': '2026-05-01T10:00:00Z',
            'thumbnail': 'https://scontent.cdninstagram.com/cover.jpg?token=source',
            'post_content': [{'type': 'Video', 'url': 'https://scontent.cdninstagram.com/film.mp4'}],
            'latest_comments': [{'comments': 'Do not publish this comment'}],
        }
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'scrape.json'
            path.write_text(json.dumps([record]), encoding='utf-8')
            call_command('import_instagram_scrape', path, stdout=StringIO())
            project = Project.objects.get(instagram_shortcode='ABC123')
            project.title = 'Manually curated title'
            project.save()
            call_command('import_instagram_scrape', path, stdout=StringIO())
        self.assertEqual(Project.objects.count(), 1)
        project.refresh_from_db()
        self.assertEqual(project.title, 'Manually curated title')
        self.assertEqual(project.media_items[0]['kind'], 'video')
        response = self.client.get(reverse('project_detail', args=[project.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manually curated title')
        self.assertContains(response, 'https://www.instagram.com/studio/')
        self.assertContains(response, '<video')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertNotContains(response, 'Do not publish this comment')
        self.assertContains(self.client.get(reverse('home')), f'href="/projects/{project.pk}/"')
        self.assertEqual(self.client.get(reverse('project_detail', args=[999999])).status_code, 404)

    def test_project_page_only_lists_current_users_collections(self):
        from collection.models import Collection
        owner = get_user_model().objects.create_user('viewer')
        other = get_user_model().objects.create_user('other-viewer')
        Collection.objects.create(title='My collection', owner=owner)
        Collection.objects.create(title='Private other collection', owner=other)
        project = Project.objects.create(title='Public project', artist='Artist', category='AI')
        self.client.force_login(owner)
        response = self.client.get(reverse('project_detail', args=[project.pk]))
        self.assertContains(response, 'My collection')
        self.assertNotContains(response, 'Private other collection')


class CoverColorTests(TestCase):
    def test_cover_colors_and_automatic_assignment(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.base import ContentFile
        from django.test import override_settings
        from archive.colors import detect_color
        for expected, rgb in [('blue', (20, 80, 240)), ('red', (240, 10, 10)), ('green', (20, 190, 40)), ('black', (0, 0, 0))]:
            buffer = BytesIO()
            Image.new('RGB', (20, 20), rgb).save(buffer, format='PNG')
            buffer.seek(0)
            self.assertEqual(detect_color(buffer), expected)
        with TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            buffer = BytesIO()
            Image.new('RGB', (20, 20), (20, 80, 240)).save(buffer, format='PNG')
            project = Project(title='Blue study', artist='Studio', category='AI')
            project.cover_file = ContentFile(buffer.getvalue(), name='blue.png')
            project.save()
            project.refresh_from_db()
            self.assertEqual(project.dominant_color, 'blue')
            response = self.client.get(reverse('home'), {'color': 'blue'})
            self.assertEqual(response.context['project_count'], 1)


class FrontendProjectDeletionTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(title='A project to review', artist='Studio', category='AI')
        self.url = reverse('project_delete', args=[self.project.pk])
        self.admin = get_user_model().objects.create_superuser('delete-admin', password='test-password')

    def test_anonymous_and_regular_members_cannot_delete(self):
        from django.contrib.auth.models import Permission
        for user in [None, get_user_model().objects.create_user('member'),
                     get_user_model().objects.create_user('staff', is_staff=True)]:
            if user is not None:
                # Even a member holding the permission must also have admin access.
                if not user.is_staff:
                    user.user_permissions.add(Permission.objects.get(codename='delete_project'))
                self.client.force_login(user)
            else:
                self.client.logout()
            with self.subTest(user=user):
                self.assertEqual(self.client.get(self.url).status_code, 403)
                self.assertEqual(self.client.post(self.url).status_code, 403)
                self.assertNotContains(self.client.get(reverse('home')), 'delete-mode-toggle')
                self.assertNotContains(self.client.get(reverse('project_detail', args=[self.project.pk])), 'DELETE PROJECT')
                self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())

    def test_confirmation_does_not_delete_and_controls_are_visible(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertContains(response, 'Delete this project?')
        self.assertContains(response, 'A project to review')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())
        self.assertContains(self.client.get(reverse('home')), 'data-delete-url=')
        self.assertContains(self.client.get(reverse('project_detail', args=[self.project.pk])), 'DELETE PROJECT')
        self.assertEqual(self.client.put(self.url).status_code, 405)

    def test_authorized_post_deletes_links_logs_action_and_redirects(self):
        from collection.models import Collection
        from django.contrib.admin.models import LogEntry, DELETION
        collection = Collection.objects.create(title='Keep this collection', owner=self.admin)
        collection.projects.add(self.project)
        submission = CurationSubmission.objects.create(source_key='instagram:delete-test',
            source_url='https://www.instagram.com/p/delete-test/', media_type='post', project=self.project)
        project_id = self.project.pk
        self.client.force_login(self.admin)
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, reverse('home'))
        self.assertContains(response, 'was deleted from the Atlas')
        self.assertFalse(Project.objects.filter(pk=project_id).exists())
        self.assertTrue(Collection.objects.filter(pk=collection.pk).exists())
        self.assertFalse(collection.projects.exists())
        submission.refresh_from_db()
        self.assertIsNone(submission.project_id)
        self.assertTrue(LogEntry.objects.filter(user=self.admin, object_id=str(project_id), action_flag=DELETION).exists())
        self.assertEqual(self.client.post(self.url).status_code, 404)

    def test_staff_with_delete_permission_can_delete_but_csrf_is_required(self):
        from django.contrib.auth.models import Permission
        from django.test import Client
        staff = get_user_model().objects.create_user('project-editor', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='delete_project'))
        client = Client(enforce_csrf_checks=True)
        client.force_login(staff)
        self.assertEqual(client.post(self.url).status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())
        self.assertEqual(client.get(self.url).status_code, 200)
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(self.url, {'csrfmiddlewaretoken': token}).status_code, 302)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())


class BulkProjectDeletionTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser('bulk-admin', password='test-password')
        self.first = Project.objects.create(title='First selection', artist='Studio', category='AI')
        self.second = Project.objects.create(title='Second selection', artist='Studio', category='AI')
        self.keep = Project.objects.create(title='Keep this project', artist='Studio', category='AI')
        self.url = reverse('projects_bulk_delete')
        self.ids = [self.first.pk, self.second.pk]

    def test_review_requires_admin_and_never_deletes(self):
        for user in [None, get_user_model().objects.create_user('bulk-member')]:
            self.client.logout()
            if user:
                self.client.force_login(user)
            for stage in ['', 'delete']:
                self.assertEqual(self.client.post(self.url, {'project_ids': self.ids, 'confirm': stage}).status_code, 403)
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {'project_ids': self.ids})
        self.assertContains(response, 'Delete 2 projects?')
        self.assertContains(response, 'First selection')
        self.assertContains(response, 'Second selection')
        self.assertNotContains(response, 'Keep this project')
        self.assertEqual(Project.objects.count(), 3)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertContains(self.client.get(reverse('project_detail', args=[self.first.pk])), 'DELETE MULTIPLE PROJECTS')

    def test_confirm_deletes_only_selected_projects_and_audits_each(self):
        from django.contrib.admin.models import LogEntry, DELETION
        from collection.models import Collection
        collection = Collection.objects.create(title='Preserved collection', owner=self.admin)
        collection.projects.add(self.first, self.second, self.keep)
        self.client.force_login(self.admin)
        response = self.client.post(self.url, {'project_ids': self.ids + [self.first.pk], 'confirm': 'delete'}, follow=True)
        self.assertContains(response, '2 projects were deleted')
        self.assertEqual(list(Project.objects.values_list('pk', flat=True)), [self.keep.pk])
        self.assertEqual(list(collection.projects.values_list('pk', flat=True)), [self.keep.pk])
        self.assertEqual(LogEntry.objects.filter(action_flag=DELETION, user=self.admin).count(), 2)

    def test_invalid_or_stale_selection_never_partially_deletes(self):
        self.client.force_login(self.admin)
        for ids in [[], ['invalid'], [self.first.pk, 999999], [str(10**50)], [self.first.pk] * 1201]:
            response = self.client.post(self.url, {'project_ids': ids, 'confirm': 'delete'})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(Project.objects.count(), 3)

    def test_csrf_required_for_review_and_confirmation(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        for stage in ['', 'delete']:
            self.assertEqual(client.post(self.url, {'project_ids': self.ids, 'confirm': stage}).status_code, 403)
        self.assertEqual(Project.objects.count(), 3)


class ProjectVideoTests(TestCase):
    def test_local_preview_is_on_atlas_and_primary_video_is_not_repeated(self):
        project = Project.objects.create(title='Moving artwork', artist='Studio', category='FILM',
            image='https://example.com/cover.jpg', media_items=[
                {'kind': 'video', 'url': '/media/projects/videos/1/source.mp4', 'preview_url': '/media/projects/videos/1/preview.mp4'},
                {'kind': 'image', 'url': '/media/extra.jpg'},
            ])
        self.assertEqual(project.preview_video_url, '/media/projects/videos/1/preview.mp4')
        home = self.client.get(reverse('home'))
        self.assertContains(home, 'data-src="/media/projects/videos/1/preview.mp4"')
        detail = self.client.get(reverse('project_detail', args=[project.pk]))
        self.assertContains(detail, '<video', count=1)
        self.assertContains(detail, 'src="/media/projects/videos/1/source.mp4"', count=1)
        self.assertNotContains(detail, '<img src="/media/projects/videos/1/source.mp4"')
        self.assertContains(detail, '/media/extra.jpg')

    def test_image_only_project_keeps_image_and_has_no_video_preview(self):
        project = Project.objects.create(title='Still image', artist='Studio', category='AI', image='https://example.com/still.jpg')
        self.assertEqual(project.preview_video_url, '')
        self.assertIsNone(project.primary_video)
        response = self.client.get(reverse('project_detail', args=[project.pk]))
        self.assertNotContains(response, '<video')
        self.assertContains(response, 'https://example.com/still.jpg')


class AtlasMapDiscoveryTests(TestCase):
    def test_creator_aliases_merge_without_merging_publisher_credits(self):
        first = Project.objects.create(title='First', artist='@priscila.nassar', category='AI', instagram_username='priscila.nassar')
        second = Project.objects.create(title='Second', artist='Priscila Nassar, published by Prosh', category='AI', instagram_username='prosh.tv_')
        Project.objects.create(title='Another artist', artist='Different Artist', category='AI', instagram_username='priscila.nassar')
        response = self.client.get(reverse('home'), {'creator': 'Priscila Nassar'})
        self.assertEqual(response.context['project_count'], 2)
        self.assertEqual(set(response.context['map_data']), {str(first.pk), str(second.pk)})
        self.assertIn(('priscila nassar', 'Priscila Nassar'), response.context['creator_choices'])
        self.assertNotIn(('@priscila.nassar', '@priscila.nassar'), response.context['creator_choices'])
        self.assertEqual(self.client.get(reverse('home'), {'creator': '@priscilanassar'}).context['project_count'], 2)

    def test_country_composes_with_filters_and_keeps_unknown_explicit(self):
        project = Project.objects.create(title='Blue place', artist='Artist', category='AI', country='Brazil', dominant_color='blue')
        Project.objects.create(title='Red place', artist='Artist', category='AI', country='Brazil', dominant_color='red')
        unknown = Project.objects.create(title='Unknown place', artist='Artist', category='AI', dominant_color='blue')
        response = self.client.get(reverse('home'), {'country': 'brazil', 'color': 'blue'})
        self.assertEqual(response.context['project_count'], 1)
        self.assertEqual(response.context['map_data'][str(project.pk)]['country'], 'Brazil')
        response = self.client.get(reverse('home'), {'country': 'undocumented'})
        self.assertEqual(set(response.context['map_data']), {str(unknown.pk)})
        self.assertEqual(response.context['map_data'][str(unknown.pk)]['country'], 'Not documented')
        self.assertEqual(self.client.get(reverse('home'), {'q':'missing'}).context['map_data'], {})

    def test_multi_credit_identity_and_map_metadata(self):
        from archive.discovery import creator_names
        p = Project(title='Collaboration', artist='Gizem Akdağ & Ege Berkina Akdağ', category='AI')
        self.assertEqual(creator_names(p), ('Gizem Akdağ', 'Ege Berkina Akdağ'))
        p.artist = 'Bruna Bismara / Touch of Oddity'
        self.assertEqual(creator_names(p), ('Bruna Bismara (Touch of Oddity)',))
