from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import BlogPost
from .models import HelpRequest


class HelpRequestModelTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='requester', password='pass')

    def test_default_values(self):
        help_request = HelpRequest.objects.create(
            user=self.user,
            subject='Need assistance',
            message='I have an issue with my account.',
        )

        self.assertEqual(help_request.status, HelpRequest.STATUS_OPEN)
        self.assertEqual(help_request.priority, HelpRequest.PRIORITY_MEDIUM)

    def test_string_representation(self):
        help_request = HelpRequest.objects.create(
            subject='Cannot post comment',
            message='Error when submitting comment.',
        )

        self.assertIn('Cannot post comment', str(help_request))
        self.assertIn('Open', str(help_request))


class HomeViewTests(TestCase):

    def setUp(self):
        self.author = get_user_model().objects.create_user(
            username='featured-author', password='pass'
        )

    def _create_post(self, **overrides):
        defaults = {
            'author': self.author,
            'title': overrides.get('title', 'Echo'),
            'body': 'Signal from the abyss',
            'status': BlogPost.STATUS_APPROVED,
            'featured': True,
            'published_at': timezone.now(),
        }
        defaults.update(overrides)
        return BlogPost.objects.create(**defaults)

    def test_home_shows_featured_posts_only(self):
        featured_post = self._create_post(title='Featured Signal')
        self._create_post(title='Hidden Signal', featured=False)
        self._create_post(title='Pending Signal',
                          status=BlogPost.STATUS_PENDING)

        response = self.client.get(reverse('pages:home'))

        self.assertContains(response, featured_post.title)
        self.assertNotContains(response, 'Hidden Signal')
        self.assertNotContains(response, 'Pending Signal')

    def test_home_orders_featured_by_published_at_desc(self):
        newer = self._create_post(
            title='Newer Signal', published_at=timezone.now())
        older = self._create_post(
            title='Older Signal',
            published_at=timezone.now() - timezone.timedelta(days=1)
        )
        fallback_recent = self._create_post(title='Fallback Recent')
        BlogPost.objects.filter(
            pk=fallback_recent.pk).update(published_at=None)
        fallback_older = self._create_post(title='Fallback Older')
        BlogPost.objects.filter(pk=fallback_older.pk).update(
            published_at=None,
            updated_at=timezone.now() - timezone.timedelta(hours=1),
        )

        response = self.client.get(reverse('pages:home'))
        featured_posts = list(response.context['featured_posts'])

        expected_order = [
            newer.title,
            older.title,
            fallback_recent.title,
            fallback_older.title,
        ]
        self.assertEqual(
            [post.title for post in featured_posts], expected_order)

    def test_home_shows_placeholder_when_no_featured(self):
        response = self.client.get(reverse('pages:home'))
        self.assertContains(response, 'Coming Soon')
