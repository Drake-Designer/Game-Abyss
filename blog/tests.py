from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import BlogPost, Comment


class BlogPostModelTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='author', password='pass'
        )

    def test_slug_unique_for_same_day_pending(self):
        """Multiple pending posts with the same title should not crash and must get unique slugs."""
        first = BlogPost.objects.create(
            author=self.user,
            title='My Duplicate Title',
            body='content',
            # status defaults to PENDING
        )
        second = BlogPost.objects.create(
            author=self.user,
            title='My Duplicate Title',
            body='another content',
            # status defaults to PENDING
        )

        self.assertNotEqual(first.slug, '')
        self.assertNotEqual(second.slug, '')
        self.assertNotEqual(first.slug, second.slug)
        self.assertTrue(second.slug.endswith('-2'))

    def test_slug_unique_for_approved_posts_same_day(self):
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

    def test_published_at_updates_with_status_transitions(self):
        """published_at is set when APPROVED and cleared when moved back to PENDING/REJECTED."""
        post = BlogPost.objects.create(
            author=self.user,
            title='Workflow Post',
            body='body',
            status=BlogPost.STATUS_PENDING,
        )
        # Initially pending → no published_at
        self.assertIsNone(post.published_at)

        # Approve → published_at set automatically
        post.status = BlogPost.STATUS_APPROVED
        post.save()
        self.assertIsNotNone(post.published_at)

        # Back to pending → published_at cleared
        post.status = BlogPost.STATUS_PENDING
        post.save()
        self.assertIsNone(post.published_at)

        # Approve again → published_at set again
        post.status = BlogPost.STATUS_APPROVED
        post.save()
        self.assertIsNotNone(post.published_at)

        # Reject → published_at cleared
        post.status = BlogPost.STATUS_REJECTED
        post.save()
        self.assertIsNone(post.published_at)


class CommentModelTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='commenter', password='pass'
        )
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
