# ============================================================
#    *** PAGES: Tests ***
# ============================================================

"""Unit tests for the Pages app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import BlogPost
from .models import HelpRequest


# ============================================================
#    *** PAGES: Tests: HelpRequest Model ***
# ============================================================


class HelpRequestModelTests(TestCase):
    """Tests for the HelpRequest model."""

    def setUp(self):
        """Create a user for associating help requests."""
        self.user = get_user_model().objects.create_user(
            username="requester", password="pass"
        )

    def test_default_values(self):
        """Ensure default status and priority are set correctly."""
        help_request = HelpRequest.objects.create(
            user=self.user,
            subject="Need assistance",
            message="I have an issue with my account.",
        )

        self.assertEqual(help_request.status, HelpRequest.STATUS_OPEN)
        self.assertEqual(help_request.priority, HelpRequest.PRIORITY_MEDIUM)

    def test_string_representation(self):
        """Ensure __str__ includes subject and human status."""
        help_request = HelpRequest.objects.create(
            subject="Cannot post comment",
            message="Error when submitting comment.",
        )

        self.assertIn("Cannot post comment", str(help_request))
        self.assertIn("Open", str(help_request))


# ============================================================
#    *** PAGES: Tests: Home View ***
# ============================================================


class HomeViewTests(TestCase):
    """Tests for the home view context and ordering."""

    def setUp(self):
        """Create a featured author for blog posts."""
        self.author = get_user_model().objects.create_user(
            username="featured-author", password="pass"
        )

    def _create_post(self, **overrides):
        """Helper to create an approved blog post with sensible defaults."""
        defaults = {
            "author": self.author,
            "title": overrides.get("title", "Echo"),
            "body": "Signal from the abyss",
            "status": BlogPost.STATUS_APPROVED,
            "featured": True,
            "published_at": timezone.now(),
        }
        defaults.update(overrides)
        return BlogPost.objects.create(**defaults)

    def test_home_separates_featured_and_latest_posts(self):
        """Featured and latest lists should be disjoint and correctly populated."""
        featured_post = self._create_post(
            title="Featured Signal", featured=True)
        latest_post = self._create_post(title="Latest Signal", featured=False)
        self._create_post(title="Pending Signal",
                          status=BlogPost.STATUS_PENDING)

        response = self.client.get(reverse("pages:home"))

        featured_titles = [
            post.title for post in response.context["featured_posts"]]
        latest_titles = [
            post.title for post in response.context["latest_posts_page"].object_list
        ]

        self.assertIn(featured_post.title, featured_titles)
        self.assertIn(latest_post.title, latest_titles)
        self.assertNotIn(latest_post.title, featured_titles)
        self.assertNotIn(featured_post.title, latest_titles)
        self.assertNotContains(response, "Pending Signal")

    def test_home_orders_featured_by_published_at_desc(self):
        """Featured posts should be ordered by published_at desc, with sensible fallbacks."""
        newer = self._create_post(
            title="Newer Signal", published_at=timezone.now())
        older = self._create_post(
            title="Older Signal",
            published_at=timezone.now() - timezone.timedelta(days=1),
        )
        fallback_recent = self._create_post(title="Fallback Recent")
        BlogPost.objects.filter(
            pk=fallback_recent.pk).update(published_at=None)
        fallback_older = self._create_post(title="Fallback Older")
        BlogPost.objects.filter(pk=fallback_older.pk).update(
            published_at=None,
            updated_at=timezone.now() - timezone.timedelta(hours=1),
        )

        response = self.client.get(reverse("pages:home"))
        featured_posts = list(
            response.context["featured_posts_page"].object_list
        )

        expected_order = [
            newer.title,
            older.title,
            fallback_recent.title,
            fallback_older.title,
        ]
        self.assertEqual(
            [post.title for post in featured_posts], expected_order)

    def test_home_orders_latest_posts_by_published_at_desc(self):
        """Latest posts list should be ordered by published_at desc, with fallbacks."""
        newer = self._create_post(
            title="Newer Latest", featured=False, published_at=timezone.now()
        )
        older = self._create_post(
            title="Older Latest",
            featured=False,
            published_at=timezone.now() - timezone.timedelta(days=1),
        )
        fallback_recent = self._create_post(
            title="Fallback Latest Recent", featured=False
        )
        BlogPost.objects.filter(
            pk=fallback_recent.pk).update(published_at=None)
        fallback_older = self._create_post(
            title="Fallback Latest Older", featured=False
        )
        BlogPost.objects.filter(pk=fallback_older.pk).update(
            published_at=None,
            updated_at=timezone.now() - timezone.timedelta(hours=1),
        )

        response = self.client.get(reverse("pages:home"))
        latest_posts = list(response.context["latest_posts_page"].object_list)

        expected_order = [
            newer.title,
            older.title,
            fallback_recent.title,
            fallback_older.title,
        ]
        self.assertEqual([post.title for post in latest_posts], expected_order)

    def test_home_shows_placeholder_when_no_featured(self):
        """Home should render a placeholder when there are no featured posts."""
        response = self.client.get(reverse("pages:home"))
        self.assertContains(response, "Coming Soon")


def test_home_posts_partial_requires_ajax_header(self):
    """The partial endpoint should reject non-AJAX requests."""

    response = self.client.get(
        reverse("pages:home_posts_partial"),
        {"section": "featured", "page": 1},
    )

    self.assertEqual(response.status_code, 400)


def test_home_posts_partial_renders_featured_posts(self):
    """Featured partial should include the featured post titles in the payload."""

    featured_post = self._create_post(title="Partial Featured")

    response = self.client.get(
        reverse("pages:home_posts_partial"),
        {"section": "featured", "page": 1},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    self.assertEqual(response.status_code, 200)
    payload = response.json()
    self.assertIn("posts_html", payload)
    self.assertIn(featured_post.title, payload["posts_html"])
    self.assertEqual(payload["page"], 1)


def test_home_posts_partial_renders_latest_posts(self):
    """Latest partial should include the latest post titles in the payload."""

    latest_post = self._create_post(title="Partial Latest", featured=False)

    response = self.client.get(
        reverse("pages:home_posts_partial"),
        {"section": "latest", "page": 1},
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )

    self.assertEqual(response.status_code, 200)
    payload = response.json()
    self.assertIn("posts_html", payload)
    self.assertIn(latest_post.title, payload["posts_html"])
    self.assertEqual(payload["page"], 1)
