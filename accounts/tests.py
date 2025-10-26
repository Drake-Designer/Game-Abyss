from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

# Create your tests here.

from blog.models import BlogPost, Comment, PostReaction, ReactionType


def _verify_email(user):
    if not user.email:
        return
    EmailAddress.objects.update_or_create(
        user=user,
        email=user.email,
        defaults={"verified": True, "primary": True},
    )


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
