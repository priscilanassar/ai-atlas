from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from archive.models import Project
from .models import Collection


class CollectionPrivacyTests(TestCase):
    def test_create_collection_with_project_from_atlas(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('create_collection'), {
            'title': 'From the Atlas', 'description': 'My selection',
            'from_atlas': '1', 'project_id': self.project.pk,
        })
        self.assertRedirects(response, reverse('home'))
        collection = Collection.objects.get(title='From the Atlas')
        self.assertEqual(collection.owner, self.owner)
        self.assertIn(self.project, collection.projects.all())

    def test_save_to_own_collection_from_atlas(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('save_project', args=[self.project.pk]), {
            'collection_id': self.own.pk, 'from_atlas': '1',
        })
        self.assertRedirects(response, reverse('home'))
        self.assertIn(self.project, self.own.projects.all())

    def setUp(self):
        self.owner = get_user_model().objects.create_user('owner')
        self.other = get_user_model().objects.create_user('other')
        self.own = Collection.objects.create(title='Private owner collection', owner=self.owner)
        self.foreign = Collection.objects.create(title='Other private collection', owner=self.other)
        self.project = Project.objects.create(title='Artwork', artist='Artist', category='AI')

    def test_collection_pages_require_login(self):
        for url in (reverse('collection'), reverse('collection_detail', args=[self.own.pk])):
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_each_user_sees_only_their_collections(self):
        for user, own, foreign in ((self.owner, self.own, self.foreign),
                                   (self.other, self.foreign, self.own)):
            self.client.force_login(user)
            for page in ('collection', 'my_collections'):
                response = self.client.get(reverse(page))
                self.assertContains(response, own.title)
                self.assertNotContains(response, foreign.title)
            self.assertEqual(self.client.get(reverse('collection_detail', args=[own.pk])).status_code, 200)
            self.assertEqual(self.client.get(reverse('collection_detail', args=[foreign.pk])).status_code, 404)

    def test_cannot_save_project_to_another_users_collection(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('save_project', args=[self.project.pk]),
                                    {'collection_id': self.foreign.pk})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(self.foreign.projects.exists())

    def test_owner_can_delete_collection_without_deleting_projects(self):
        self.own.projects.add(self.project)
        self.client.force_login(self.owner)
        url = reverse('delete_collection', args=[self.own.pk])
        self.assertContains(self.client.get(url), 'Delete this collection?')
        self.assertTrue(Collection.objects.filter(pk=self.own.pk).exists())
        self.assertContains(self.client.get(reverse('my_collections')), 'Delete collection Private owner collection')
        self.assertRedirects(self.client.post(url), reverse('my_collections'))
        self.assertFalse(Collection.objects.filter(pk=self.own.pk).exists())
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())
        self.assertTrue(Collection.objects.filter(pk=self.foreign.pk).exists())

    def test_collection_delete_is_private_and_csrf_protected(self):
        from django.test import Client
        url = reverse('delete_collection', args=[self.own.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        self.client.force_login(self.other)
        for method in (self.client.get, self.client.post):
            self.assertEqual(method(url).status_code, 404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.put(url).status_code, 405)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(url).status_code, 403)
        client.get(url)
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post(url, {'csrfmiddlewaretoken': token}).status_code, 302)

    def test_staff_admin_is_also_scoped_to_owner(self):
        self.owner.is_staff = True
        self.owner.save()
        self.owner.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='collection', codename__in=[
                'view_collection', 'change_collection', 'delete_collection']))
        self.client.force_login(self.owner)
        response = self.client.get(reverse('admin:collection_collection_changelist'))
        self.assertContains(response, self.own.title)
        self.assertNotContains(response, self.foreign.title)
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.context['collection_count'], 1)
        self.client.post(reverse('admin:collection_collection_delete', args=[self.foreign.pk]), {'post': 'yes'})
        self.assertTrue(Collection.objects.filter(pk=self.foreign.pk).exists())
