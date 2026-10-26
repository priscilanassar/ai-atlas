from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from archive.models import Project
from collection.models import Collection
from datetime import date


class HomeGlobeTests(TestCase):
    def test_search_controls_and_map_menu_are_separate(self):
        response = self.client.get(reverse('home'))
        for field in ('search', 'creator', 'sort'):
            self.assertContains(response, f'id="atlas-{field}"')
        for field in ('country', 'type', 'color', 'format', 'field', 'tool'):
            self.assertNotContains(response, f'id="atlas-{field}"')
        self.assertNotContains(response, 'data-view="orbit"')
        self.assertContains(response, '<option value="orbit">3D Orbit</option>')
        self.assertNotContains(response, 'Letter index')
        self.assertNotContains(response, 'Country islands')
        self.assertNotContains(response, 'Creator constellations')

    def test_name_color_and_country_filters_combine_without_city(self):
        target = Project.objects.create(title='Ocean Studies', artist='Studio', category='AI',
                                         country='Brazil', city='São Paulo', dominant_color='blue')
        Project.objects.create(title='Ocean Elsewhere', artist='Studio', category='AI', dominant_color='red')
        response = self.client.get(reverse('home'), {'q': 'ocean', 'color': 'blue', 'country': 'brazil', 'city': 'ignored'})
        self.assertEqual(response.context['project_count'], 1)
        self.assertEqual([tile['project'] for tile in response.context['tiles'] if tile['project']], [target])
        self.assertNotContains(response, 'id="atlas-country"')
        self.assertNotContains(response, 'atlas-city')
        self.assertNotContains(response, 'CREATIVE DNA')
        response = self.client.get(reverse('home'), {'q': 'no matching title'})
        self.assertEqual(response.context['project_count'], 0)
        self.assertContains(response, 'No projects match your filters')

    def test_atlas_sorting_and_color_filter(self):
        zulu = Project.objects.create(title='Zulu', artist='Artist', category='AI', year=2020,
                                      dominant_color='blue', project_date=date(2024, 6, 1))
        alpha = Project.objects.create(title='alpha', artist='Artist', category='AI', year=2023,
                                       dominant_color='red')
        unassigned = Project.objects.create(title='Middle', artist='Artist', category='AI', year=2025)
        def visible(**params):
            response = self.client.get(reverse('home'), params)
            self.assertEqual(response.status_code, 200)
            return list(dict.fromkeys(tile['project'] for tile in response.context['tiles'] if tile['project']))
        self.assertEqual(visible(sort='name_asc'), [alpha, unassigned, zulu])
        self.assertEqual(visible(sort='name_desc'), [zulu, unassigned, alpha])
        self.assertEqual(visible(sort='date_desc'), [unassigned, zulu, alpha])
        self.assertEqual(visible(sort='date_asc'), [alpha, zulu, unassigned])
        self.assertEqual(visible(sort='color'), [alpha, zulu, unassigned])
        self.assertEqual(visible(color='blue'), [zulu])
        self.assertEqual(visible(color='unassigned'), [unassigned])
        self.assertEqual(visible(color='purple'), [])
        self.assertEqual(visible(sort='invalid', color='invalid'), [unassigned, zulu, alpha])

    def test_atlas_and_legacy_archive_lead_to_home(self):
        self.assertRedirects(self.client.get(reverse('atlas')), reverse('home'))
        self.assertRedirects(self.client.get(reverse('archive')), reverse('home'))

    def test_atlas_exposes_only_current_users_collections(self):
        owner = get_user_model().objects.create_user('atlas-owner')
        other = get_user_model().objects.create_user('other-owner')
        own = Collection.objects.create(title='My atlas collection', owner=owner)
        Collection.objects.create(title='Someone elses collection', owner=other)
        self.client.force_login(owner)
        response = self.client.get(reverse('home'))
        self.assertEqual(list(response.context['collections']), [own])
        self.assertContains(response, 'CREATE COLLECTION')

    def test_empty_archive_has_original_dense_globe(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.context['tiles']), 1400)
        self.assertTrue(all(tile['project'] is None for tile in response.context['tiles']))

    def test_projects_replace_placeholders_and_have_details(self):
        project = Project.objects.create(title='Globe artwork', artist='Artist', category='AI',
                                         description='A real project description')
        response = self.client.get(reverse('home'))
        self.assertIn(project, [tile['project'] for tile in response.context['tiles']])
        self.assertContains(response, f'data-project="project-{project.pk}"')
        self.assertContains(response, 'A real project description')
        self.assertEqual(sum(tile['project'] == project for tile in response.context['tiles']), 1)
        self.assertEqual(response.context['project_count'], 1)

    def test_globe_contains_each_project_once(self):
        Project.objects.bulk_create([Project(title=f'Artwork {i}', artist='Studio', category='AI') for i in range(150)])
        response = self.client.get(reverse('home'))
        ids = [tile['project'].pk for tile in response.context['tiles'] if tile['project']]
        self.assertEqual(len(ids), 150)
        self.assertEqual(len(set(ids)), 150)

    def test_dense_globe_keeps_same_outline_after_catalogue_changes(self):
        from .globe_layout import build_globe_tiles
        original = build_globe_tiles([])
        for count in (1, 7, 13, 29, 136, 150, 200, 1200):
            with self.subTest(count=count):
                projects = list(range(count))
                tiles = build_globe_tiles(projects)
                self.assertEqual([tile['project'] for tile in tiles if tile['project'] is not None], projects)
                coordinates = {(tile['x'], tile['y']) for tile in tiles}
                self.assertEqual(len(coordinates), len(original))
                self.assertEqual(coordinates, {(tile['x'],tile['y']) for tile in original})
                self.assertTrue(all(6 <= x <= 94 and 6 <= y <= 94 for x, y in coordinates))
                self.assertTrue({(50, 6), (6, 50), (94, 50), (50, 94)} <= coordinates)



class AtlasAdminTests(TestCase):
    def test_superuser_can_delete_users_collections_and_projects(self):
        admin = get_user_model().objects.create_superuser('admin', password='test-password')
        member = get_user_model().objects.create_user('member')
        collection = Collection.objects.create(title='Collection to delete', owner=member)
        project = Project.objects.create(title='Project to delete', artist='Artist', category='AI')
        self.client.force_login(admin)
        for model, obj, route in (
            (Collection, collection, 'admin:collection_collection_delete'),
            (Project, project, 'admin:archive_project_delete'),
            (get_user_model(), member, 'admin:auth_user_delete'),
        ):
            with self.subTest(route=route):
                url = reverse(route, args=[obj.pk])
                self.assertEqual(self.client.get(url).status_code, 200)
                self.assertTrue(model.objects.filter(pk=obj.pk).exists())
                response = self.client.post(url, {'post': 'yes'})
                self.assertEqual(response.status_code, 302)
                self.assertFalse(model.objects.filter(pk=obj.pk).exists())

    def test_anonymous_visitors_see_branded_login(self):
        response = self.client.get(reverse('admin:index'))
        self.assertRedirects(response, reverse('admin:login') + '?next=/admin/')
        response = self.client.get(reverse('admin:login'))
        self.assertContains(response, 'css/admin.css')
        self.assertContains(response, 'AI WITH VISION.')

    def test_superuser_can_browse_dashboard_and_project_forms(self):
        user = get_user_model().objects.create_superuser('curator', password='test-password')
        Project.objects.create(title='Atlas experiment', artist='Artist', category='AI')
        self.client.force_login(user)
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.context['project_count'], 1)
        self.assertContains(response, 'Atlas experiment')
        self.assertContains(response, 'Add project')
        for url in ('admin:archive_project_changelist', 'admin:archive_project_add',
                    'admin:collection_collection_add', 'admin:auth_user_changelist'):
            with self.subTest(url=url):
                response = self.client.get(reverse(url))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'css/admin.css')

    def test_staff_without_permissions_cannot_see_projects(self):
        user = get_user_model().objects.create_user('staff', password='test-password', is_staff=True)
        Project.objects.create(title='Restricted project', artist='Artist', category='AI')
        self.client.force_login(user)
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['project_count'])
        self.assertNotContains(response, 'Restricted project')
        self.assertEqual(self.client.get(reverse('admin:archive_project_changelist')).status_code, 403)
