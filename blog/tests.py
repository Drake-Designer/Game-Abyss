from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import BlogPost, Comment


class BlogPostModelTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='author', password='pass')

    def test_slug_unique_for_same_day_drafts(self):
        """Multiple drafts with the same title should not crash and get unique slugs."""

        first = BlogPost.objects.create(
            author=self.user,
            title='My Duplicate Title',
            body='content')
        second = BlogPost.objects.create(
            author=self.user,
            title='My Duplicate Title',
            body='another content')

        self.assertNotEqual(first.slug, '')
        self.assertNotEqual(second.slug, '')
        self.assertNotEqual(first.slug, second.slug)
        self.assertTrue(second.slug.endswith('-2'))

    def test_slug_unique_for_published_posts_same_day(self):
        """Approved posts on the same day also receive a unique slug suffix."""

        now = timezone.now()
        post_one = BlogPost.objects.create(
            author=self.user,
            title='Launch Day',
            body='body',
            status=BlogPost.STATUS_APPROVED,
            published_at=now,
        )
        post_two = BlogPost.objects.create(
            author=self.user,
            title='Launch Day',
            body='body',
            status=BlogPost.STATUS_APPROVED,
            published_at=now,
        )

        self.assertTrue(post_two.slug.endswith('-2'))
        self.assertNotEqual(post_one.slug, post_two.slug)


class CommentModelTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='commenter', password='pass')
        self.post = BlogPost.objects.create(
            author=self.user,
            title='Test Post',
            body='content',
        )

    def test_default_status_is_pending(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            body='Nice article!',
        )
        self.assertEqual(comment.status, Comment.STATUS_PENDING)

    def test_approved_manager_filters_status(self):
        pending = Comment.objects.create(
            post=self.post,
            author=self.user,
            body='Pending comment',
        )
        approved = Comment.objects.create(
            post=self.post,
            author=self.user,
            body='Approved comment',
            status=Comment.STATUS_APPROVED,
        )

        approved_comments = Comment.approved.all()

        self.assertIn(approved, approved_comments)
        self.assertNotIn(pending, approved_comments)
