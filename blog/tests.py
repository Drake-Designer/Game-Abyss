# /* ============================================================
#    *** BLOG: Tests ***
#    ============================================================ */
"""Exercise blog app behavior."""
# pylint: disable=too-many-lines

# /* ============================================================
#    *** BLOG: Tests: Imports ***
#    ============================================================ */
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import BlogPost, Comment, CommentReport, PostReaction, ReactionType


# /* ============================================================
#    *** BLOG: Tests: Helpers ***
#    ============================================================ */
def verify_users(*users):
    """Mark provided users as verified."""
    for user in users:
        email = getattr(user, "email", "") or ""
        if not email:
            continue
        EmailAddress.objects.update_or_create(
            user=user,
            email=email,
            defaults={"verified": True, "primary": True},
        )


# /* ============================================================
#    *** BLOG: Tests: Blog Post Model Tests ***
#    ============================================================ */
class BlogPostModelTests(TestCase):
    """Verify blog post model helpers."""

    def setUp(self):
        """Create a test author."""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="author", password="pass")

    def test_slug_unique_for_same_day_pending(self):
        """Ensure pending posts with same title get unique slugs."""
        first = BlogPost.objects.create(
            author=self.user,
            title="My Duplicate Title",
            body="content",
        )
        second = BlogPost.objects.create(
            author=self.user,
            title="My Duplicate Title",
            body="another content",
        )

        self.assertNotEqual(first.slug, "")
        self.assertNotEqual(second.slug, "")
        self.assertNotEqual(first.slug, second.slug)
        self.assertTrue(second.slug.endswith("-2"))

    def test_slug_unique_for_approved_posts_same_day(self):
        """Ensure approved posts on same day get unique slugs."""
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
        """Ensure published_at tracks status transitions."""
        post = BlogPost.objects.create(
            author=self.user,
            title="Workflow Post",
            body="body",
            status=BlogPost.STATUS_PENDING,
        )
        self.assertIsNone(post.published_at)

        post.status = BlogPost.STATUS_APPROVED
        post.save()
        self.assertIsNotNone(post.published_at)

        post.status = BlogPost.STATUS_PENDING
        post.save()
        self.assertIsNone(post.published_at)

        post.status = BlogPost.STATUS_APPROVED
        post.save()
        self.assertIsNotNone(post.published_at)

        post.status = BlogPost.STATUS_DRAFT
        post.save()
        self.assertIsNone(post.published_at)

        post.status = BlogPost.STATUS_APPROVED
        post.save()
        self.assertIsNotNone(post.published_at)

        post.status = BlogPost.STATUS_REJECTED
        post.save()
        self.assertIsNone(post.published_at)


# /* ============================================================
#    *** BLOG: Tests: Draft Workflow View Tests ***
#    ============================================================ */
class DraftWorkflowViewTests(TestCase):
    """Verify draft workflow views."""

    def setUp(self):
        """Create users for draft workflow scenarios."""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="drafty",
            email="drafty@example.com",
            password="pass",
        )
        self.staff = user_model.objects.create_user(
            username="draft_staff",
            email="draft-staff@example.com",
            password="pass",
            is_staff=True,
        )
        self.other = user_model.objects.create_user(
            username="lurker",
            email="lurker@example.com",
            password="pass",
        )
        verify_users(self.user, self.staff)

    def test_new_post_can_be_saved_as_draft(self):
        """Ensure users can save a new draft post."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("blog:new"),
            {
                "title": "Draft Title",
                "body": "Draft body",
                "excerpt": "",
                "tags": "",
                "action": "save_draft",
            },
        )
        post = BlogPost.objects.get(title="Draft Title")
        self.assertEqual(post.status, BlogPost.STATUS_DRAFT)
        self.assertRedirects(response, reverse(
            "blog:edit_post", args=[post.pk]))

    def test_new_post_publish_sets_pending_for_regular_user(self):
        """Ensure publishing sets pending for regular users."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("blog:new"),
            {
                "title": "Pending Title",
                "body": "Pending body",
                "excerpt": "",
                "tags": "",
                "action": "publish",
            },
        )
        post = BlogPost.objects.get(title="Pending Title")
        self.assertEqual(post.status, BlogPost.STATUS_PENDING)
        self.assertRedirects(response, reverse("blog:index"))

    def test_new_post_publish_sets_approved_for_staff(self):
        """Ensure staff publishing approves the post."""
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("blog:new"),
            {
                "title": "Staff Title",
                "body": "Staff body",
                "excerpt": "",
                "tags": "",
                "action": "publish",
            },
        )
        post = BlogPost.objects.get(title="Staff Title")
        self.assertEqual(post.status, BlogPost.STATUS_APPROVED)
        self.assertRedirects(response, reverse("blog:index"))

    def test_draft_post_visibility(self):
        """Ensure draft visibility respects permissions."""
        post = BlogPost.objects.create(
            author=self.user,
            title="Hidden Draft",
            body="Top secret",
            status=BlogPost.STATUS_DRAFT,
        )
        detail_url = post.get_absolute_url()

        self.client.force_login(self.user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["show_engagement"])
        self.assertIsNone(response.context["comment_form"])
        self.assertNotContains(response, "Post Reactions")
        self.assertNotContains(response, "Submit Comment")
        self.client.logout()

        self.client.force_login(self.other)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        self.client.force_login(self.staff)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["show_engagement"])
        self.assertNotContains(response, "Post Reactions")
        self.assertNotContains(response, "Submit Comment")

    def test_published_post_keeps_engagement_sections(self):
        """Ensure published posts still render reactions and comments."""
        post = BlogPost.objects.create(
            author=self.user,
            title="Live Post",
            body="Ready for the world",
            status=BlogPost.STATUS_APPROVED,
        )
        detail_url = post.get_absolute_url()

        self.client.force_login(self.other)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_engagement"])
        self.assertContains(response, "Post Reactions")
        self.assertContains(response, "Comments")

    def test_staff_edit_draft_hides_author_field(self):
        """Verify staff do not see author field when editing drafts."""
        draft = BlogPost.objects.create(
            author=self.staff,
            title="Staff Draft",
            body="Classified",
            status=BlogPost.STATUS_DRAFT,
        )
        edit_url = reverse("blog:edit_post", args=[draft.pk])

        self.client.force_login(self.staff)
        response = self.client.get(edit_url)
        form = response.context["form"]
        self.assertNotIn("author", form.fields)
        self.assertNotContains(response, 'id="id_author"')

    def test_staff_edit_published_retains_author_field(self):
        """Ensure staff retain author field when editing non-drafts."""
        post = BlogPost.objects.create(
            author=self.staff,
            title="Published",
            body="Visible",
            status=BlogPost.STATUS_APPROVED,
        )
        edit_url = reverse("blog:edit_post", args=[post.pk])

        self.client.force_login(self.staff)
        response = self.client.get(edit_url)
        form = response.context["form"]
        self.assertIn("author", form.fields)
        self.assertContains(response, 'id="id_author"')


# /* ============================================================
#    *** BLOG: Tests: Comment Model Tests ***
#    ============================================================ */
class CommentModelTests(TestCase):
    """Verify comment model behavior."""

    def setUp(self):
        """Create a user and base post."""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="commenter", password="pass")
        self.post = BlogPost.objects.create(
            author=self.user,
            title="Test Post",
            body="content",
        )

    def test_default_status_is_pending(self):
        """Ensure new comments start as pending."""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            body="Nice article!",
        )
        self.assertEqual(comment.status, Comment.STATUS_PENDING)

    def test_approved_manager_filters_status(self):
        """Ensure approved manager filters pending comments."""
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


# /* ============================================================
#    *** BLOG: Tests: Notification Email Tests ***
#    ============================================================ */
class NotificationEmailTests(TestCase):
    """Verify notification emails fire correctly."""

    def setUp(self):
        """Create users used for email notifications."""
        user_model = get_user_model()
        self.team = user_model.objects.create_superuser(
            username="council",
            email="team.gameabyss@gmail.com",
            password="pass",
        )
        self.author = user_model.objects.create_user(
            username="author", email="author@example.com", password="pass"
        )
        self.commenter = user_model.objects.create_user(
            username="commenter", email="commenter@example.com", password="pass"
        )
        verify_users(self.team, self.author, self.commenter)

    def test_post_creation_sends_notification_email(self):
        """Ensure creating a post sends a notification email."""
        mail.outbox = []
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
        """Ensure creating a comment sends a notification email."""
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
        """Ensure reporting a comment sends a notification email."""
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


# /* ============================================================
#    *** BLOG: Tests: Comment Report Flow Tests ***
#    ============================================================ */
class CommentReportFlowTests(TestCase):
    """Verify comment reporting flow."""

    def setUp(self):
        """Create staff, reporter, and author users."""
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.reporter = user_model.objects.create_user(
            username="reporter", email="reporter@example.com", password="pass"
        )
        self.comment_author = user_model.objects.create_user(
            username="comment_author", email="commenter@example.com", password="pass"
        )
        verify_users(self.staff, self.reporter, self.comment_author)

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
        """Ensure reporting creates a single record and email."""
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

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(report_url, payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CommentReport.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)


# /* ============================================================
#    *** BLOG: Tests: Auto Approval Tests ***
#    ============================================================ */
class AutoApprovalTests(TestCase):
    """Verify auto approval rules for staff."""

    def setUp(self):
        """Create staff and superuser accounts."""
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.superuser = user_model.objects.create_superuser(
            username="overlord", email="overlord@example.com", password="pass"
        )
        verify_users(self.staff, self.superuser)

    def test_staff_post_and_comment_auto_approved(self):
        """Ensure staff posts and comments auto approve."""
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
        """Ensure superuser posts and comments auto approve."""
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


# /* ============================================================
#    *** BLOG: Tests: Comment Moderation UI Tests ***
#    ============================================================ */
class CommentModerationUITests(TestCase):
    """Verify moderation controls in the UI."""

    def setUp(self):
        """Create users and content for moderation tests."""
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.post_author = user_model.objects.create_user(
            username="poster", email="poster@example.com", password="pass"
        )
        self.comment_author = user_model.objects.create_user(
            username="commenter", email="commenter@example.com", password="pass"
        )
        verify_users(self.staff, self.post_author, self.comment_author)

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
        """Ensure staff see delete control instead of report."""
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


# /* ============================================================
#    *** BLOG: Tests: Comment Deletion Permissions Tests ***
#    ============================================================ */
class CommentDeletionPermissionsTests(TestCase):
    """Verify deletion permissions for comments."""

    def setUp(self):
        """Create staff and user comments for deletion checks."""
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.user_one = user_model.objects.create_user(
            username="userone", email="userone@example.com", password="pass"
        )
        self.user_two = user_model.objects.create_user(
            username="usertwo", email="usertwo@example.com", password="pass"
        )
        verify_users(self.staff, self.user_one, self.user_two)

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
        """Ensure users can only delete their own comments."""
        self.client.login(username="userone", password="pass")
        other_delete_url = reverse(
            "blog:delete_comment", args=[self.comment_two.pk])
        response = self.client.post(
            other_delete_url, {"next": self.post.get_absolute_url()}
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "errors/403.html")
        self.assertTrue(Comment.objects.filter(
            pk=self.comment_two.pk).exists())

        own_delete_url = reverse("blog:delete_comment", args=[
                                 self.comment_one.pk])
        response = self.client.post(
            own_delete_url, {"next": self.post.get_absolute_url()}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(
            pk=self.comment_one.pk).exists())

    def test_staff_can_delete_any_comment(self):
        """Ensure staff can delete any comment."""
        self.client.login(username="staff", password="pass")
        delete_url = reverse("blog:delete_comment", args=[self.comment_two.pk])
        response = self.client.post(
            delete_url, {"next": self.post.get_absolute_url()}
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(
            pk=self.comment_two.pk).exists())


# /* ============================================================
#    *** BLOG: Tests: Post Deletion Tests ***
#    ============================================================ */
class PostDeletionTests(TestCase):
    """Verify deletion permissions for posts."""

    def setUp(self):
        """Create users and a post for deletion scenarios."""
        user_model = get_user_model()
        self.author = user_model.objects.create_user(
            username="author", email="author@example.com", password="pass"
        )
        self.regular = user_model.objects.create_user(
            username="regular", email="regular@example.com", password="pass"
        )
        self.staff = user_model.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.superuser = user_model.objects.create_superuser(
            username="admin", email="admin@example.com", password="pass"
        )
        verify_users(self.author, self.regular, self.staff, self.superuser)

        self.post = BlogPost.objects.create(
            author=self.author,
            title="Delete Me",
            body="Content",
            status=BlogPost.STATUS_APPROVED,
        )

    def test_author_can_delete_own_post(self):
        """Ensure authors can delete their own posts."""
        self.client.login(username="author", password="pass")
        response = self.client.post(
            reverse("blog:delete_post", args=[self.post.pk]))
        self.assertRedirects(response, reverse("blog:index"))
        self.assertFalse(BlogPost.objects.filter(pk=self.post.pk).exists())

    def test_regular_user_cannot_delete_others_post(self):
        """Ensure regular users cannot delete others' posts."""
        self.client.login(username="regular", password="pass")
        response = self.client.post(
            reverse("blog:delete_post", args=[self.post.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "errors/403.html")
        self.assertTrue(BlogPost.objects.filter(pk=self.post.pk).exists())

    def test_staff_can_delete_any_post(self):
        """Ensure staff can delete any post."""
        self.client.login(username="staff", password="pass")
        response = self.client.post(
            reverse("blog:delete_post", args=[self.post.pk]))
        self.assertRedirects(response, reverse("blog:index"))
        self.assertFalse(BlogPost.objects.filter(pk=self.post.pk).exists())

    def test_delete_button_visibility(self):
        """Ensure delete button visibility matches permissions."""
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


# /* ============================================================
#    *** BLOG: Tests: Post and Comment Edit Permissions Tests ***
#    ============================================================ */
class PostCommentEditPermissionsTests(TestCase):
    """Verify edit permissions for posts and comments."""

    def setUp(self):
        """Create users, a post, and a comment for edit checks."""
        user_model = get_user_model()
        self.author = user_model.objects.create_user(
            username="author", email="author@example.com", password="pass"
        )
        self.other = user_model.objects.create_user(
            username="other", email="other@example.com", password="pass"
        )
        self.staff = user_model.objects.create_user(
            username="staff", email="staff@example.com", password="pass", is_staff=True
        )
        self.superuser = user_model.objects.create_superuser(
            username="admin", email="admin@example.com", password="pass"
        )
        verify_users(self.author, self.other, self.staff, self.superuser)
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
        """Ensure authors can edit their own posts."""
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
        """Ensure other users cannot edit the post."""
        self.client.login(username="other", password="pass")
        response = self.client.get(
            reverse("blog:edit_post", args=[self.post.pk]))
        self.assertEqual(response.status_code, 403)

    def test_staff_cannot_edit_other_users_post(self):
        """Ensure staff cannot edit another user's post."""
        self.client.login(username="staff", password="pass")
        response = self.client.get(
            reverse("blog:edit_post", args=[self.post.pk]))
        self.assertEqual(response.status_code, 403)

    def test_superuser_cannot_edit_other_users_post(self):
        """Ensure superusers cannot edit another user's post."""
        self.client.login(username="admin", password="pass")
        response = self.client.get(
            reverse("blog:edit_post", args=[self.post.pk]))
        self.assertEqual(response.status_code, 403)

    def test_author_can_edit_own_comment(self):
        """Ensure authors can edit their own comments."""
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
        """Ensure other users cannot edit the comment."""
        self.client.login(username="other", password="pass")
        response = self.client.get(
            reverse("blog:edit_comment", args=[self.comment.pk]))
        self.assertEqual(response.status_code, 403)

    def test_staff_cannot_edit_other_users_comment(self):
        """Ensure staff cannot edit another user's comment."""
        self.client.login(username="staff", password="pass")
        response = self.client.get(
            reverse("blog:edit_comment", args=[self.comment.pk]))
        self.assertEqual(response.status_code, 403)

    def test_superuser_cannot_edit_other_users_comment(self):
        """Ensure superusers cannot edit another user's comment."""
        self.client.login(username="admin", password="pass")
        response = self.client.get(
            reverse("blog:edit_comment", args=[self.comment.pk]))
        self.assertEqual(response.status_code, 403)

    def test_staff_and_superuser_can_edit_their_own_posts_and_comments(self):
        """Ensure staff and superusers can edit their own content."""
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


# /* ============================================================
#    *** BLOG: Tests: Content Creation Access Tests ***
#    ============================================================ */
class ContentCreationAccessTests(TestCase):
    """Verify access control for new post creation."""

    def setUp(self):
        """Create a verified user for access checks."""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="creator", email="creator@example.com", password="pass"
        )
        verify_users(self.user)

    def test_new_post_requires_authentication(self):
        """Ensure anonymous users are redirected from new post."""
        new_url = reverse("blog:new")
        response = self.client.get(new_url)
        login_url = reverse("account_login")
        self.assertRedirects(response, f"{login_url}?next={new_url}")

    def test_authenticated_user_can_access_new_post(self):
        """Ensure authenticated users can view new post form."""
        self.client.login(username="creator", password="pass")
        response = self.client.get(reverse("blog:new"))
        self.assertEqual(response.status_code, 200)


# /* ============================================================
#    *** BLOG: Tests: Email Verification Enforcement Tests ***
#    ============================================================ */
class EmailVerificationEnforcementTests(TestCase):
    """Verify actions enforced by email verification."""

    def setUp(self):
        """Create users with varying email verification states."""
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="verifier", email="verifier@example.com", password="pass"
        )
        self.other = user_model.objects.create_user(
            username="author", email="author@example.com", password="pass"
        )
        verify_users(self.other)

        self.post = BlogPost.objects.create(
            author=self.other,
            title="Verification Post",
            body="Content",
            status=BlogPost.STATUS_APPROVED,
        )

        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=False,
        )
        self.client.force_login(self.user)

    def test_unverified_user_redirected_from_new_post(self):
        """Ensure unverified users are redirected from new post."""
        response = self.client.get(reverse("blog:new"))
        self.assertRedirects(response, reverse("account_email"))

    def test_unverified_user_cannot_comment(self):
        """Ensure unverified users cannot post comments."""
        response = self.client.post(
            self.post.get_absolute_url(), {"body": "Hi"})
        self.assertRedirects(response, reverse("account_email"))
        self.assertFalse(Comment.objects.filter(body="Hi").exists())

    def test_unverified_user_cannot_react(self):
        """Ensure unverified users cannot add reactions."""
        react_url = reverse("blog:react_post", args=[self.post.pk])
        response = self.client.post(
            react_url,
            {"reaction": ReactionType.LIKE.value,
                "next": self.post.get_absolute_url()},
        )
        self.assertRedirects(response, reverse("account_email"))
        self.assertFalse(
            PostReaction.objects.filter(
                user=self.user, post=self.post).exists()
        )

    def test_actions_allowed_after_email_verified(self):
        """Ensure verified users can perform content actions."""
        EmailAddress.objects.filter(user=self.user).update(verified=True)

        response = self.client.get(reverse("blog:new"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            self.post.get_absolute_url(),
            {"body": "Verified comment"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Comment.objects.filter(
            body="Verified comment").exists())

        react_url = reverse("blog:react_post", args=[self.post.pk])
        response = self.client.post(
            react_url,
            {"reaction": ReactionType.LIKE.value,
                "next": self.post.get_absolute_url()},
        )
        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertTrue(
            PostReaction.objects.filter(
                user=self.user, post=self.post).exists()
        )
