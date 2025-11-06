# ============================================================
#   *** GALLERY: Tests ***
# ============================================================

from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import GalleryImage


class GalleryModelTests(TestCase):
    """Exercise GalleryImage model behaviors."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="uploader",
            email="uploader@example.com",
            password="secret",
        )

    def _fake_image(self, name="test.jpg"):
        # Minimal JPEG header is enough for tests
        return SimpleUploadedFile(name, b"\xff\xd8\xff", content_type="image/jpeg")

    def test_mark_featured_sets_status_and_timestamp(self):
        """Featuring an image auto-approves it and sets featured_at."""
        img = GalleryImage.objects.create(
            image=self._fake_image(),
            uploaded_by=self.user,
            title="Thumb",
            status=GalleryImage.Status.PENDING,
            is_featured=True,
        )
        # After save in model.save(), mark_featured() should run
        img.refresh_from_db()
        self.assertEqual(img.status, GalleryImage.Status.APPROVED)
        self.assertIsNotNone(img.featured_at)

    def test_unfeature_clears_featured_at(self):
        """Removing featured flag clears featured_at timestamp."""
        img = GalleryImage.objects.create(
            image=self._fake_image("feat.jpg"),
            uploaded_by=self.user,
            title="Feat",
            status=GalleryImage.Status.APPROVED,
            is_featured=True,
        )
        self.assertIsNotNone(img.featured_at)

        # Unfeature then save should clear timestamp
        img.is_featured = False
        img.save()
        img.refresh_from_db()
        self.assertIsNone(img.featured_at)

    def test_queryset_featured_orders_by_featured_at_then_created(self):
        """Featured queryset returns approved featured images ordered by recency."""
        older = GalleryImage.objects.create(
            image=self._fake_image("old.jpg"),
            uploaded_by=self.user,
            title="Old",
            status=GalleryImage.Status.APPROVED,
            is_featured=True,
        )
        # Force featured_at older
        older.featured_at = timezone.now() - timezone.timedelta(days=1)
        older.save(update_fields=["featured_at"])

        newer = GalleryImage.objects.create(
            image=self._fake_image("new.jpg"),
            uploaded_by=self.user,
            title="New",
            status=GalleryImage.Status.APPROVED,
            is_featured=True,
        )

        featured = list(GalleryImage.objects.featured())
        self.assertEqual(featured[0].pk, newer.pk)
        self.assertEqual(featured[1].pk, older.pk)

    def test_delete_removes_file_from_storage(self):
        """Deleting an image removes the stored file."""
        img = GalleryImage.objects.create(
            image=self._fake_image("cleanup.jpg"),
            uploaded_by=self.user,
            title="Cleanup",
            status=GalleryImage.Status.APPROVED,
        )
        image_field = img.image
        with mock.patch.object(image_field, "delete") as delete_mock:
            img.delete()
        delete_mock.assert_called_once_with(save=False)


class GalleryViewTests(TestCase):
    """Exercises for gallery management views."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="member", email="member@example.com", password="secret"
        )
        self.other = get_user_model().objects.create_user(
            username="other", email="other@example.com", password="secret"
        )
        self.staff = get_user_model().objects.create_user(
            username="moderator",
            email="mod@example.com",
            password="secret",
            is_staff=True,
        )

    def _fake_image(self, name="view.jpg"):
        return SimpleUploadedFile(name, b"\xff\xd8\xff", content_type="image/jpeg")

    def test_my_images_requires_login(self):
        url = reverse("gallery:my_images")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/accounts/login/", res.url)

    def test_my_images_lists_only_user_uploads(self):
        own = GalleryImage.objects.create(
            image=self._fake_image("mine.jpg"),
            uploaded_by=self.user,
            title="Mine",
            status=GalleryImage.Status.PENDING,
        )
        GalleryImage.objects.create(
            image=self._fake_image("other.jpg"),
            uploaded_by=self.other,
            title="Other",
            status=GalleryImage.Status.APPROVED,
        )
        self.client.force_login(self.user)
        res = self.client.get(reverse("gallery:my_images"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, own.title)
        self.assertNotContains(res, "Other")

    def test_delete_allows_owner(self):
        image = GalleryImage.objects.create(
            image=self._fake_image("delete.jpg"),
            uploaded_by=self.user,
            title="Delete me",
            status=GalleryImage.Status.APPROVED,
        )
        self.client.force_login(self.user)
        res = self.client.post(reverse("gallery:delete", args=[image.pk]))
        self.assertRedirects(res, reverse("gallery:my_images"))
        self.assertFalse(GalleryImage.objects.filter(pk=image.pk).exists())

    def test_delete_blocks_non_owner(self):
        image = GalleryImage.objects.create(
            image=self._fake_image("block.jpg"),
            uploaded_by=self.user,
            title="Block",
            status=GalleryImage.Status.APPROVED,
        )
        self.client.force_login(self.other)
        res = self.client.post(reverse("gallery:delete", args=[image.pk]))
        self.assertEqual(res.status_code, 403)
        self.assertTrue(GalleryImage.objects.filter(pk=image.pk).exists())

    def test_delete_allows_staff_for_any_image(self):
        image = GalleryImage.objects.create(
            image=self._fake_image("staff.jpg"),
            uploaded_by=self.user,
            title="Staff",
            status=GalleryImage.Status.APPROVED,
        )
        self.client.force_login(self.staff)
        res = self.client.post(reverse("gallery:delete", args=[image.pk]))
        self.assertRedirects(res, reverse("gallery:my_images"))
        self.assertFalse(GalleryImage.objects.filter(pk=image.pk).exists())
