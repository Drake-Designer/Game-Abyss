from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import BlogPost, Comment, CommentReport


class BlogPostModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="author", password="pass"
        )

    def test_slug_unique_for_same_day_pending(self):
        """Multiple pending posts with the same title should not crash and must get unique slugs."""
        first = BlogPost.objects.create(
            author=self.user,
            title="My Duplicate Title",
            body="content",
            # status defaults to PENDING
        )
        second = BlogPost.objects.create(
            author=self.user,
            title="My Duplicate Title",
            body="another content",
            # status defaults to PENDING
        )

        self.assertNotEqual(first.slug, "")
        self.assertNotEqual(second.slug, "")
        self.assertNotEqual(first.slug, second.slug)
        self.assertTrue(second.slug.endswith("-2"))

    def test_slug_unique_for_approved_posts_same_day(self):
        """Approved posts on the same day also receive a unique slug suffix."""
        now = timezone.now()
        post_one = BlogPost.objects.create(
            author=self.user,
            title="Launch Day",
            body="body",
            status=BlogPost.STATUS_APPROVED,
            published_at=now,
        )
        post_two = BlogPost.objects.create(
            author=self.user,
            title="Launch Day",
            body="body",
            status=BlogPost.STATUS_APPROVED,
            published_at=now,
        )

        self.assertTrue(post_two.slug.endswith("-2"))
        self.assertNotEqual(post_one.slug, post_two.slug)

    def test_published_at_updates_with_status_transitions(self):
        """published_at is set when APPROVED and cleared when moved back to PENDING or REJECTED."""
        post = BlogPost.objects.create(
            author=self.user,
            title="Workflow Post",
            body="body",
            status=BlogPost.STATUS_PENDING,
        )
        # Initially pending -> no published_at
        self.assertIsNone(post.published_at)

        # Approve -> published_at set automatically
        post.status = BlogPost.STATUS_APPROVED
        post.save()
        self.assertIsNotNone(post.published_at)

        # Back to pending -> published_at cleared
        post.status = BlogPost.STATUS_PENDING
        post.save()
        self.assertIsNone(post.published_at)

        # Approve again -> published_at set again
        post.status = BlogPost.STATUS_APPROVED
        post.save()
        self.assertIsNotNone(post.published_at)

        # Reject -> published_at cleared
        post.status = BlogPost.STATUS_REJECTED
        post.save()
        self.assertIsNone(post.published_at)


class CommentModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="commenter", password="pass"
        )
        self.post = BlogPost.objects.create(
            author=self.user,
            title="Test Post",
            body="content",
        )

    def test_default_status_is_pending(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            body="Nice article!",
        )
        self.assertEqual(comment.status, Comment.STATUS_PENDING)

    def test_approved_manager_filters_status(self):
        pending = Comment.objects.create(
            post=self.post,
            author=self.user,
            body="Pending comment",
        )
        approved = Comment.objects.create(
            post=self.post,
            author=self.user,
            body="Approved comment",
            status=Comment.STATUS_APPROVED,
        )

        approved_comments = Comment.approved.all()

        self.assertIn(approved, approved_comments)
        self.assertNotIn(pending, approved_comments)


class NotificationEmailTests(TestCase):
    def setUp(self):
        User = get_user_model()
        # Ensure there is at least one superuser with the target email
        self.team = User.objects.create_superuser(
            username="council",
            email="team.gameabyss@gmail.com",
            password="pass",
        )
        self.author = User.objects.create_user(
            username="author", email="author@example.com", password="pass"
        )
        self.commenter = User.objects.create_user(
            username="commenter", email="commenter@example.com", password="pass"
        )

    def test_post_creation_sends_notification_email(self):
        mail.outbox = []
        # Execute on_commit callbacks immediately inside tests
        with self.captureOnCommitCallbacks(execute=True):
            BlogPost.objects.create(
                author=self.author,
                title="Signal",
                body="Content of the abyss",
            )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["team.gameabyss@gmail.com"])
        self.assertIn("New post submitted", email.subject)

    def test_comment_creation_sends_notification_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            post = BlogPost.objects.create(
                author=self.author,
                title="Commented Post",
                body="Content",
            )
        mail.outbox = []
        with self.captureOnCommitCallbacks(execute=True):
            Comment.objects.create(
                post=post,
                author=self.commenter,
                body="First!",
            )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["team.gameabyss@gmail.com"])
        self.assertIn("New comment submitted", email.subject)

    def test_comment_report_sends_notification_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            post = BlogPost.objects.create(
                author=self.author,
                title="Report Post",
                body="Content",
            )
        with self.captureOnCommitCallbacks(execute=True):
            comment = Comment.objects.create(
                post=post,
                author=self.commenter,
                body="Needs review",
                status=Comment.STATUS_APPROVED,
            )
        mail.outbox = []
        with self.captureOnCommitCallbacks(execute=True):
            CommentReport.objects.create(
                comment=comment,
                reported_by=self.author,
                reason=CommentReport.Reason.SPAM,
            )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("team.gameabyss@gmail.com", email.to)
        self.assertIn("Comment reported", email.subject)


class CommentReportFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.reporter = User.objects.create_user(
            username="reporter", email="reporter@example.com", password="pass"
        )
        self.comment_author = User.objects.create_user(
            username="comment_author", email="commenter@example.com", password="pass"
        )

        self.post = BlogPost.objects.create(
            author=self.comment_author,
            title="Reportable Post",
            body="Content",
            status=BlogPost.STATUS_APPROVED,
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.comment_author,
            body="Problematic comment",
            status=Comment.STATUS_APPROVED,
        )

    def test_report_creates_single_record_and_single_email(self):
        self.client.login(username="reporter", password="pass")
        report_url = reverse("blog:report_comment", args=[self.comment.pk])
        payload = {
            "reason": CommentReport.Reason.SPAM,
            "next": self.post.get_absolute_url(),
        }

        mail.outbox = []
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(report_url, payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CommentReport.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        # Second attempt should not create a duplicate report or new email
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(report_url, payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CommentReport.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)


class AutoApprovalTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.superuser = User.objects.create_superuser(
            username="overlord", email="overlord@example.com", password="pass"
        )

    def test_staff_post_and_comment_auto_approved(self):
        self.client.login(username="staff", password="pass")
        response = self.client.post(
            reverse("blog:new"),
            {"title": "Staff Signal", "body": "Approved content"},
        )
        self.assertEqual(response.status_code, 302)
        post = BlogPost.objects.latest("id")
        self.assertEqual(post.status, BlogPost.STATUS_APPROVED)

        response = self.client.post(
            post.get_absolute_url(),
            {"body": "Staff moderation skip"},
        )
        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.latest("id")
        self.assertEqual(comment.status, Comment.STATUS_APPROVED)
        self.assertEqual(comment.author, self.staff)

    def test_superuser_post_and_comment_auto_approved(self):
        self.client.login(username="overlord", password="pass")
        response = self.client.post(
            reverse("blog:new"),
            {"title": "Overlord Signal", "body": "Approved immediately"},
        )
        self.assertEqual(response.status_code, 302)
        post = BlogPost.objects.latest("id")
        self.assertEqual(post.status, BlogPost.STATUS_APPROVED)

        response = self.client.post(
            post.get_absolute_url(),
            {"body": "Overlord comment"},
        )
        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.latest("id")
        self.assertEqual(comment.status, Comment.STATUS_APPROVED)
        self.assertEqual(comment.author, self.superuser)


class CommentModerationUITests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.post_author = User.objects.create_user(
            username="poster", email="poster@example.com", password="pass"
        )
        self.comment_author = User.objects.create_user(
            username="commenter", email="commenter@example.com", password="pass"
        )

        self.post = BlogPost.objects.create(
            author=self.post_author,
            title="UI Test Post",
            body="Content",
            status=BlogPost.STATUS_APPROVED,
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.comment_author,
            body="Hello there",
            status=Comment.STATUS_APPROVED,
        )

    def test_staff_see_delete_action_instead_of_report(self):
        self.client.login(username="staff", password="pass")
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("blog:delete_comment", args=[self.comment.pk]),
        )
        self.assertNotContains(
            response,
            reverse("blog:report_comment", args=[self.comment.pk]),
        )


class CommentDeletionPermissionsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.user_one = User.objects.create_user(
            username="userone", email="userone@example.com", password="pass"
        )
        self.user_two = User.objects.create_user(
            username="usertwo", email="usertwo@example.com", password="pass"
        )

        self.post = BlogPost.objects.create(
            author=self.staff,
            title="Deletion Test Post",
            body="Content",
            status=BlogPost.STATUS_APPROVED,
        )
        self.comment_one = Comment.objects.create(
            post=self.post,
            author=self.user_one,
            body="First comment",
            status=Comment.STATUS_APPROVED,
        )
        self.comment_two = Comment.objects.create(
            post=self.post,
            author=self.user_two,
            body="Second comment",
            status=Comment.STATUS_APPROVED,
        )

    def test_regular_user_can_delete_only_own_comment(self):
        self.client.login(username="userone", password="pass")
        other_delete_url = reverse(
            "blog:delete_comment", args=[self.comment_two.pk])
        response = self.client.post(
            other_delete_url, {"next": self.post.get_absolute_url()})
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "errors/403.html")
        self.assertTrue(Comment.objects.filter(
            pk=self.comment_two.pk).exists())

        own_delete_url = reverse("blog:delete_comment", args=[
                                 self.comment_one.pk])
        response = self.client.post(
            own_delete_url, {"next": self.post.get_absolute_url()})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(
            pk=self.comment_one.pk).exists())

    def test_staff_can_delete_any_comment(self):
        self.client.login(username="staff", password="pass")
        delete_url = reverse("blog:delete_comment", args=[self.comment_two.pk])
        response = self.client.post(
            delete_url, {"next": self.post.get_absolute_url()})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(
            pk=self.comment_two.pk).exists())


class PostDeletionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(
            username="author", email="author@example.com", password="pass"
        )
        self.regular = User.objects.create_user(
            username="regular", email="regular@example.com", password="pass"
        )
        self.staff = User.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="pass"
        )

        self.post = BlogPost.objects.create(
            author=self.author,
            title="Delete Me",
            body="Content",
            status=BlogPost.STATUS_APPROVED,
        )

    def test_author_can_delete_own_post(self):
        self.client.login(username="author", password="pass")
        response = self.client.post(
            reverse("blog:delete_post", args=[self.post.pk])
        )
        self.assertRedirects(response, reverse("blog:index"))
        self.assertFalse(BlogPost.objects.filter(pk=self.post.pk).exists())

    def test_regular_user_cannot_delete_others_post(self):
        self.client.login(username="regular", password="pass")
        response = self.client.post(
            reverse("blog:delete_post", args=[self.post.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "errors/403.html")
        self.assertTrue(BlogPost.objects.filter(pk=self.post.pk).exists())

    def test_staff_can_delete_any_post(self):
        self.client.login(username="staff", password="pass")
        response = self.client.post(
            reverse("blog:delete_post", args=[self.post.pk])
        )
        self.assertRedirects(response, reverse("blog:index"))
        self.assertFalse(BlogPost.objects.filter(pk=self.post.pk).exists())

    def test_delete_button_visibility(self):
        detail_url = self.post.get_absolute_url()
        delete_url = reverse("blog:delete_post", args=[self.post.pk])
        scenarios = [
            ("author", True),
            ("staff", True),
            ("admin", True),
            ("regular", False),
            (None, False),
        ]

        for username, should_see in scenarios:
            with self.subTest(user=username):
                self.client.logout()
                if username:
                    self.client.login(username=username, password="pass")
                response = self.client.get(detail_url)
                if should_see:
                    self.assertContains(response, delete_url)
                else:
                    self.assertNotContains(response, delete_url)


class PostCommentEditPermissionsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(
            username="author", email="author@example.com", password="pass"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="pass"
        )
        self.staff = User.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="pass"
        )
        self.post = BlogPost.objects.create(
            author=self.author,
            title="Editable Post",
            body="Content",
            status=BlogPost.STATUS_APPROVED,
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            body="Editable Comment",
            status=Comment.STATUS_APPROVED,
        )

    def test_author_can_edit_own_post(self):
        self.client.login(username="author", password="pass")
        response = self.client.post(
            reverse("blog:edit_post", args=[self.post.pk]),
            {
                "title": "Updated Title",
                "excerpt": "Excerpt",
                "body": "Updated content",
                "tags": "rpg",
                "next": reverse("blog:index"),
            },
        )
        self.assertRedirects(response, reverse("blog:index"))
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Updated Title")

    def test_other_user_cannot_edit_post(self):
        self.client.login(username="other", password="pass")
        response = self.client.get(
            reverse("blog:edit_post", args=[self.post.pk]))
        self.assertEqual(response.status_code, 403)

    def test_author_can_edit_own_comment(self):
        self.client.login(username="author", password="pass")
        response = self.client.post(
            reverse("blog:edit_comment", args=[self.comment.pk]),
            {
                "body": "Updated comment body",
                "next": self.post.get_absolute_url(),
            },
        )
        self.assertRedirects(response, self.post.get_absolute_url())
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.body, "Updated comment body")

    def test_other_user_cannot_edit_comment(self):
        self.client.login(username="other", password="pass")
        response = self.client.get(
            reverse("blog:edit_comment", args=[self.comment.pk]))
        self.assertEqual(response.status_code, 403)

    def test_staff_and_superuser_can_edit_their_own_posts_and_comments(self):
        # Staff edits own post
        staff_post = BlogPost.objects.create(
            author=self.staff,
            title="Staff Post",
            body="Body",
            status=BlogPost.STATUS_APPROVED,
        )
        self.client.login(username="staff", password="pass")
        response = self.client.post(
            reverse("blog:edit_post", args=[staff_post.pk]),
            {
                "title": "Staff Updated",
                "body": "Updated body",
                "tags": "",
                "status": BlogPost.STATUS_APPROVED,
                "next": reverse("blog:index"),
            },
        )
        self.assertRedirects(response, reverse("blog:index"))
        staff_post.refresh_from_db()
        self.assertEqual(staff_post.title, "Staff Updated")

        # Superuser edits own comment
        super_post = BlogPost.objects.create(
            author=self.superuser,
            title="Super Post",
            body="Body",
            status=BlogPost.STATUS_APPROVED,
        )
        super_comment = Comment.objects.create(
            post=super_post,
            author=self.superuser,
            body="Super comment",
            status=Comment.STATUS_APPROVED,
        )
        self.client.logout()
        self.client.login(username="admin", password="pass")
        response = self.client.post(
            reverse("blog:edit_comment", args=[super_comment.pk]),
            {"body": "Super updated", "next": super_post.get_absolute_url()},
        )
        self.assertRedirects(response, super_post.get_absolute_url())
        super_comment.refresh_from_db()
        self.assertEqual(super_comment.body, "Super updated")
