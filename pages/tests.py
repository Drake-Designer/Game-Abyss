# ============================================================
#    *** PAGES: Tests ***
# ============================================================

"""Tests for pages views and homepage JSON partials without code duplication."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from gallery.models import GalleryImage
from pages import (
    HOME_FEATURED_POST_LIMIT,
    HOME_FEATURED_GALLERY_LIMIT,
    HOME_OTHER_POSTS_PER_PAGE,
    home_posts_queryset,
)
from pages.models import HelpRequest
from blog.models import BlogPost

User = get_user_model()


class HomeHelperTests(TestCase):
    """Unit tests for the shared home helpers imported from pages package."""

    def setUp(self):
        self.author = User.objects.create_user(
            username="author", email="a@example.com", password="pass"
        )

    def test_home_posts_queryset_filters_by_featured_and_status(self):
        """home_posts_queryset must respect featured flag and APPROVED status."""
        BlogPost.objects.create(
            title="feat approved",
            body="x",
            author=self.author,
            status=BlogPost.STATUS_APPROVED,
            featured=True,
        )
        BlogPost.objects.create(
            title="feat pending",
            body="x",
            author=self.author,
            status=BlogPost.STATUS_PENDING,
            featured=True,
        )
        BlogPost.objects.create(
            title="latest approved",
            body="x",
            author=self.author,
            status=BlogPost.STATUS_APPROVED,
            featured=False,
        )

        featured = list(home_posts_queryset(featured=True))
        latest = list(home_posts_queryset(featured=False))

        self.assertEqual(len(featured), 1)
        self.assertEqual(featured[0].title, "feat approved")
        self.assertEqual(len(latest), 1)
        self.assertEqual(latest[0].title, "latest approved")


class HomeViewTests(TestCase):
    """Integration tests for HomeView context and pagination."""

    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(
            username="author", email="a@example.com", password="pass"
        )

        # Approved featured posts
        for i in range(HOME_FEATURED_POST_LIMIT + 2):
            BlogPost.objects.create(
                title=f"F{i}",
                body="f body",
                author=self.author,
                status=BlogPost.STATUS_APPROVED,
                featured=True,
            )

        # Approved latest posts
        for i in range(HOME_OTHER_POSTS_PER_PAGE + 3):
            BlogPost.objects.create(
                title=f"L{i}",
                body="l body",
                author=self.author,
                status=BlogPost.STATUS_APPROVED,
                featured=False,
            )

        # Featured gallery images
        for i in range(HOME_FEATURED_GALLERY_LIMIT + 5):
            GalleryImage.objects.create(
                image=f"gallery/{i}.jpg",
                uploaded_by=self.author,
                is_featured=True,
                status=GalleryImage.Status.APPROVED,
            )

    def test_home_view_context_has_featured_latest_and_gallery(self):
        url = reverse("pages:home")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        self.assertIn("featured_posts_page", res.context)
        fp = res.context["featured_posts_page"]
        self.assertLessEqual(fp.paginator.per_page, HOME_FEATURED_POST_LIMIT)

        self.assertIn("latest_posts_page", res.context)
        lp = res.context["latest_posts_page"]
        self.assertLessEqual(lp.paginator.per_page, HOME_OTHER_POSTS_PER_PAGE)

        self.assertIn("hero_gallery_images", res.context)
        self.assertLessEqual(
            len(res.context["hero_gallery_images"]
                ), HOME_FEATURED_GALLERY_LIMIT
        )

    def test_featured_pagination_query_param(self):
        url = reverse("pages:home")
        res = self.client.get(url, {"featured_page": 2})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["featured_posts_page"].number, 2)

    def test_latest_pagination_query_param(self):
        url = reverse("pages:home")
        res = self.client.get(url, {"latest_page": 2})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["latest_posts_page"].number, 2)


class HomePostsPartialViewTests(TestCase):
    """Tests for AJAX JSON partial that paginates home sections."""

    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(
            username="author", email="a@example.com", password="pass"
        )

        for i in range(8):
            BlogPost.objects.create(
                title=f"F{i}",
                body="f body",
                author=self.author,
                status=BlogPost.STATUS_APPROVED,
                featured=True,
            )
            BlogPost.objects.create(
                title=f"L{i}",
                body="l body",
                author=self.author,
                status=BlogPost.STATUS_APPROVED,
                featured=False,
            )

    def _ajax_get(self, params):
        url = reverse("pages:home_posts_partial")
        return self.client.get(url, params, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_rejects_non_ajax(self):
        url = reverse("pages:home_posts_partial")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 400)

    def test_unknown_section_is_bad_request(self):
        res = self._ajax_get({"section": "oops", "page": 1})
        self.assertEqual(res.status_code, 400)

    def test_featured_section_returns_html_and_page_number(self):
        res = self._ajax_get({"section": "featured", "page": 1})
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertIn("posts_html", payload)
        self.assertIn("pagination_html", payload)
        self.assertEqual(payload["page"], 1)

    def test_latest_section_uses_latest_page_param_name(self):
        res = self._ajax_get({"section": "latest", "page": 2})
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertIn("posts_html", payload)
        self.assertIn("pagination_html", payload)
        self.assertEqual(payload["page"], 2)


class StaticViewsTests(TestCase):
    """About and Contact pages basic behavior."""

    def setUp(self):
        self.client = Client()

    def test_about_view_renders(self):
        url = reverse("pages:about")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_contact_get_renders_form(self):
        url = reverse("pages:contact")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "<form", html=False)

    def test_contact_post_valid_creates_help_request(self):
        url = reverse("pages:contact")
        data = {
            "name": "Alice",
            "email": "alice@example.com",
            "subject": "Help",
            "message": "I need assistance",
            "priority": HelpRequest.PRIORITY_MEDIUM,
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(
            HelpRequest.objects.filter(email="alice@example.com").exists()
        )

    def test_contact_post_invalid_shows_errors(self):
        url = reverse("pages:contact")
        res = self.client.post(url, {})
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Please", res.content)
