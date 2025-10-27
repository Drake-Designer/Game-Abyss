from datetime import date

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.formats import date_format

from blog.models import BlogPost, Comment, PostReaction, ReactionType

from .models import UserProfile


def _verify_email(user):
    if not user.email:
        return
    EmailAddress.objects.update_or_create(
        user=user,
        email=user.email,
        defaults={"verified": True, "primary": True},
    )


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ProfileEditEmailTests(TestCase):
    def setUp(self):
        mail.outbox.clear()

    def _post_profile_form(self, user, email):
        self.client.force_login(user)
        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "first_name": "",
                "last_name": "",
                "email": email,
                "date_of_birth": "",
                "bio": "",
            },
        )
        return response

    def test_user_without_email_can_add_one_and_requires_verification(self):
        user = get_user_model().objects.create_user(
            username="noemail", password="test-pass"
        )

        response = self._post_profile_form(user, "new@example.com")

        self.assertRedirects(
            response,
            reverse("accounts:profile", args=[user.username]),
        )

        user.refresh_from_db()
        self.assertEqual(user.email, "new@example.com")

        email_record = EmailAddress.objects.get(user=user)
        self.assertEqual(email_record.email, "new@example.com")
        self.assertFalse(email_record.verified)
        self.assertTrue(email_record.primary)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("new@example.com", mail.outbox[0].to)

    def test_email_change_requires_reverification(self):
        user = get_user_model().objects.create_user(
            username="withmail",
            email="old@example.com",
            password="test-pass",
        )
        EmailAddress.objects.create(
            user=user,
            email="old@example.com",
            primary=True,
            verified=True,
        )

        response = self._post_profile_form(user, "updated@example.com")

        self.assertRedirects(
            response,
            reverse("accounts:profile", args=[user.username]),
        )

        user.refresh_from_db()
        self.assertEqual(user.email, "updated@example.com")

        email_records = EmailAddress.objects.filter(user=user)
        self.assertEqual(email_records.count(), 1)
        email_record = email_records.get()
        self.assertEqual(email_record.email, "updated@example.com")
        self.assertFalse(email_record.verified)
        self.assertTrue(email_record.primary)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("updated@example.com", mail.outbox[0].to)


class ProfileDeleteViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="deleteme",
            email="deleteme@example.com",
            password="super-secret",
        )
        self.post = BlogPost.objects.create(
            title="Sample post",
            body="Content",
            author=self.user,
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            body="Comment body",
        )
        self.reaction = PostReaction.objects.create(
            post=self.post,
            user=self.user,
            reaction=ReactionType.LIKE,
        )
        _verify_email(self.user)

    def test_requires_correct_password(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile_delete"),
            {"confirm_password": "wrong-password"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            get_user_model().objects.filter(username="deleteme").exists()
        )

    def test_deletes_user_and_related_content_with_correct_password(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:profile_delete"),
            {"confirm_password": "super-secret"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(username="deleteme").exists()
        )
        self.assertFalse(BlogPost.objects.filter(pk=self.post.pk).exists())
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())
        self.assertFalse(PostReaction.objects.filter(
            pk=self.reaction.pk).exists())


class EmailVerificationRequirementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="pending", email="pending@example.com", password="secret",
        )
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=False,
        )
        self.client.force_login(self.user)

    def test_profile_delete_redirects_when_email_unverified(self):
        response = self.client.get(reverse("accounts:profile_delete"))
        self.assertRedirects(response, reverse("account_email"))

    def test_password_change_redirects_when_email_unverified(self):
        response = self.client.get(reverse("account_change_password"))
        self.assertRedirects(response, reverse("account_email"))

    def test_access_allowed_after_verification(self):
        EmailAddress.objects.filter(user=self.user).update(verified=True)

        response = self.client.get(reverse("accounts:profile_delete"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("account_change_password"))
        self.assertEqual(response.status_code, 200)


class ProfileDraftVisibilityTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(
            username="author", email="author@example.com", password="secret"
        )
        self.other_user = get_user_model().objects.create_user(
            username="reader", email="reader@example.com", password="secret"
        )
        self.staff_user = get_user_model().objects.create_user(
            username="mod", email="mod@example.com", password="secret", is_staff=True
        )
        self.draft_post = BlogPost.objects.create(
            title="Hidden draft",
            body="Draft content",
            author=self.author,
            status=BlogPost.STATUS_DRAFT,
        )
        self.published_post = BlogPost.objects.create(
            title="Visible post",
            body="Published content",
            author=self.author,
            status=BlogPost.STATUS_APPROVED,
        )

    def test_author_can_see_draft_section(self):
        self.client.force_login(self.author)

        response = self.client.get(
            reverse("accounts:profile", args=[self.author.username])
        )

        self.assertContains(response, 'data-testid="draft-posts"')
        self.assertContains(response, "Hidden draft")
        self.assertContains(response, "Continue editing")
        self.assertContains(response, "Visible post")

    def test_other_user_cannot_see_drafts(self):
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse("accounts:profile", args=[self.author.username])
        )

        self.assertContains(response, "Visible post")
        self.assertNotContains(response, "Hidden draft")
        self.assertNotContains(response, 'data-testid="draft-posts"')
        self.assertNotContains(response, "Edit profile")
        self.assertNotContains(response, "Delete account")

    def test_staff_user_cannot_see_drafts(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse("accounts:profile", args=[self.author.username])
        )

        self.assertContains(response, "Visible post")
        self.assertNotContains(response, "Hidden draft")
        self.assertNotContains(response, 'data-testid="draft-posts"')
        self.assertNotContains(response, "Edit profile")
        self.assertNotContains(response, "Delete account")

    def test_staff_owner_sees_moderation_tools_placeholder(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse("accounts:profile", args=[self.staff_user.username])
        )

        self.assertContains(response, "Staff tools")
        self.assertContains(response, "moderation and admin")


class ProfilePublicViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.author = User.objects.create_user(
            username="profile_author",
            email="profile_author@example.com",
            password="secret",
        )
        self.viewer = User.objects.create_user(
            username="profile_viewer",
            email="profile_viewer@example.com",
            password="secret",
        )
        self.author.first_name = "Aurora"
        self.author.last_name = "Vega"
        self.author.save(update_fields=["first_name", "last_name"])
        self.author_profile = UserProfile.objects.create(
            user=self.author,
            date_of_birth=date(1992, 7, 16),
            bio="Charting nebulae and new horizons.",
        )

        self.approved_post = BlogPost.objects.create(
            title="Approved spotlight",
            body="Public content",
            author=self.author,
            status=BlogPost.STATUS_APPROVED,
        )
        self.pending_post = BlogPost.objects.create(
            title="Pending showcase",
            body="Pending content",
            author=self.author,
            status=BlogPost.STATUS_PENDING,
        )
        self.draft_post = BlogPost.objects.create(
            title="Draft idea",
            body="Draft content",
            author=self.author,
            status=BlogPost.STATUS_DRAFT,
        )
        self.approved_comment = Comment.objects.create(
            post=self.approved_post,
            author=self.author,
            body="Approved feedback",
            status=Comment.STATUS_APPROVED,
        )
        self.pending_comment = Comment.objects.create(
            post=self.approved_post,
            author=self.author,
            body="Pending feedback",
            status=Comment.STATUS_PENDING,
        )

    def test_profile_url_pattern(self):
        self.assertEqual(
            reverse("accounts:profile", args=[self.author.username]),
            f"/u/{self.author.username}/",
        )

    def test_public_profile_shows_only_public_content(self):
        response = self.client.get(
            reverse("accounts:profile", args=[self.author.username])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.approved_post.title)
        self.assertNotContains(response, self.pending_post.title)
        self.assertNotContains(response, self.draft_post.title)
        self.assertContains(response, "Approved feedback")
        self.assertNotContains(response, "Pending feedback")
        self.assertContains(response, 'data-testid="public-post-count">1')
        self.assertContains(response, 'data-testid="approved-comment-count">1')

    def test_public_profile_shows_profile_metadata(self):
        response = self.client.get(
            reverse("accounts:profile", args=[self.author.username])
        )

        formatted_dob = date_format(
            self.author_profile.date_of_birth, "F j, Y"
        )
        joined = date_format(self.author.date_joined, "F j, Y")
        self.assertContains(response, "Nickname")
        self.assertContains(response, self.author.username)
        self.assertContains(response, "Member since")
        self.assertContains(response, joined)
        self.assertContains(response, "Full name")
        self.assertContains(response, "Aurora Vega")
        self.assertContains(response, formatted_dob)
        self.assertContains(response, "Bio")
        self.assertContains(response, self.author_profile.bio)
        self.assertContains(response, "Activity status")
        self.assertContains(response, "Last active")
        self.assertNotContains(response, "No activity recorded")

    def test_profile_hides_role_badge_for_regular_user(self):
        response = self.client.get(
            reverse("accounts:profile", args=[self.author.username])
        )

        self.assertNotContains(response, 'data-testid="role-badge"')

    def test_profile_shows_role_badge_for_staff_user(self):
        staff_user = get_user_model().objects.create_user(
            username="staffer",
            email="staffer@example.com",
            password="secret",
            is_staff=True,
        )
        UserProfile.objects.create(user=staff_user)

        response = self.client.get(
            reverse("accounts:profile", args=[staff_user.username])
        )

        self.assertContains(response, 'data-testid="role-badge"')
        self.assertContains(response, "Staff")

    def test_profile_shows_admin_badge_for_superuser(self):
        admin_user = get_user_model().objects.create_superuser(
            username="overseer",
            email="overseer@example.com",
            password="secret",
        )
        UserProfile.objects.create(user=admin_user)

        response = self.client.get(
            reverse("accounts:profile", args=[admin_user.username])
        )

        self.assertContains(response, 'data-testid="role-badge"')
        self.assertContains(response, "Super Admin")

    def test_profile_owner_sees_their_role_badge(self):
        admin_user = get_user_model().objects.create_superuser(
            username="stellar", email="stellar@example.com", password="secret"
        )
        UserProfile.objects.create(user=admin_user)
        self.client.force_login(admin_user)

        response = self.client.get(
            reverse("accounts:profile", args=[admin_user.username])
        )

        self.assertContains(response, 'data-testid="role-badge"')
        self.assertContains(response, "Super Admin")

    def test_authenticated_user_can_open_other_profile(self):
        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("accounts:profile", args=[self.author.username])
        )

        self.assertEqual(response.status_code, 200)

    def test_profile_404_for_unknown_user(self):
        response = self.client.get(reverse("accounts:profile", args=["ghost"]))

        self.assertEqual(response.status_code, 404)


class ProfileFavoritesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="favuser",
            email="fav@example.com",
            password="secret",
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            favorite_games="Half-Life, Dark Souls",
            favorite_genres="RPG, Horror"
        )

    def test_favorites_render_in_profile(self):
        response = self.client.get(
            reverse("accounts:profile", args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Favorites")
        self.assertContains(response, "Half-Life")
        self.assertContains(response, "RPG")

    def test_favorites_section_hidden_if_empty(self):
        empty_user = get_user_model().objects.create_user(
            username="nofav",
            email="nofav@example.com",
            password="secret",
        )
        UserProfile.objects.create(user=empty_user)

        response = self.client.get(
            reverse("accounts:profile", args=[empty_user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Favorites")
