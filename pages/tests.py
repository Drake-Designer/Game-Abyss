from django.contrib.auth import get_user_model
from django.test import TestCase

# Create your tests here.

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
