from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from archive.models import Project


class DiscoveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.film = Project.objects.create(
            title='Ocean Campaign', artist='Alice & Bob', category='FILM',
            description='A commissioned campaign.', dominant_color='blue',
            tools='Dreamina Seedance 2.0; Kling 2.6', year=2025)
        cls.series = Project.objects.create(
            title='Ocean Portrait Series', artist='Carol, published by Studio', category='AI',
            description='Independent research.', tools='Kling 2.5', year=2024,
            media_items=[{'kind': 'image'}, {'kind': 'image'}])
        cls.override = Project.objects.create(
            title='Architecture Campaign', artist='Alice', category='DESIGN',
            project_type='art', media_format='image', creative_field='abstract', year=2023)

    def results(self, **params):
        response = self.client.get(reverse('home'), params)
        self.assertEqual(response.status_code, 200)
        projects = [tile['project'] for tile in response.context['tiles'] if tile['project']]
        self.assertEqual(response.context['project_count'], len(projects))
        self.assertEqual(len(projects), len(set(projects)))
        return projects, response

    def test_all_filters_combine_and_keep_selections(self):
        projects, response = self.results(q='ocean', color='blue', type='brand', format='video',
                                         field='film', creator='BOB', tool='seedance', sort='name_asc')
        self.assertEqual(projects, [self.film])
        for key, value in [('project_type', 'brand'), ('media_format', 'video'),
                           ('creative_field', 'film'), ('creator', 'bob'), ('tool', 'seedance')]:
            self.assertEqual(response.context[key], value)
        self.assertTrue(response.context['has_filters'])
        self.assertEqual(self.results(type='brand', format='image')[0], [])

    def test_curator_overrides_and_existing_project_inference(self):
        self.assertEqual(self.results(type='art', format='image', field='abstract')[0], [self.override])
        self.assertEqual(self.results(type='experiment', format='series')[0], [self.series])
        self.assertEqual(self.results(field='architecture')[0], [])

    def test_creator_credits_and_tool_versions_are_searchable(self):
        self.assertEqual(self.results(creator='bob')[0], [self.film])
        self.assertEqual(self.results(creator='carol')[0], [self.series])
        self.assertEqual(self.results(tool='kling')[0], [self.film, self.series])
        self.assertEqual(self.results(tool='undisclosed')[0], [self.override])
        _, response = self.results(creator='alice', tool='dreamina')
        self.assertIn(('carol', 'Carol'), response.context['creator_choices'])
        self.assertIn(('kling', 'Kling'), response.context['tool_choices'])
        self.assertNotIn(('studio', 'Studio'), response.context['creator_choices'])

    def test_invalid_filters_do_not_hide_the_catalogue(self):
        projects, response = self.results(type='unknown', format='unknown', field='unknown',
                                         creator='unknown', tool='unknown')
        self.assertEqual(len(projects), 3)
        self.assertFalse(response.context['has_filters'])

    def test_admin_filters_match_inferred_and_curated_labels(self):
        self.client.force_login(get_user_model().objects.create_superuser('curator', password='test'))
        response = self.client.get(reverse('admin:archive_project_changelist'),
                                   {'discovery_type': 'brand', 'discovery_format': 'video'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['cl'].queryset), [self.film])
        response = self.client.get(reverse('admin:archive_project_change', args=[self.override.pk]))
        for field in ('project_type', 'media_format', 'creative_field'):
            self.assertContains(response, f'name="{field}"')
