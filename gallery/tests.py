# ============================================================
#   *** GALLERY: Tests ***
# ============================================================

from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import GalleryImage


@override_settings(
    DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage',
    MEDIA_ROOT='test_media'
)
class GalleryModelTests(TestCase):
    """Exercise GalleryImage model behaviors."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="uploader",
            email="uploader@example.com",
            password="secret",
        )

    def _fake_image(self, name="test.jpg"):
        # Create a minimal valid JPEG image for testing
        # This is a 1x1 pixel red JPEG
        jpeg_data = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
            b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
            b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00'
            b'\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01'
            b'\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07'
            b'\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05'
            b'\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07'
            b'"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18'
            b'\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86'
            b'\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6'
            b'\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6'
            b'\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5'
            b'\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00'
            b'\x08\x01\x01\x00\x00?\x00\xfb\xfe\x0f\xa2\x8a(\xff\xd9'
        )
        return SimpleUploadedFile(name, jpeg_data, content_type="image/jpeg")

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


@override_settings(
    DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage',
    MEDIA_ROOT='test_media'
)
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
        # Create a minimal valid JPEG image for testing
        # This is a 1x1 pixel red JPEG
        jpeg_data = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
            b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
            b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00'
            b'\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01'
            b'\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07'
            b'\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05'
            b'\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07'
            b'"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18'
            b'\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86'
            b'\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6'
            b'\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6'
            b'\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5'
            b'\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00'
            b'\x08\x01\x01\x00\x00?\x00\xfb\xfe\x0f\xa2\x8a(\xff\xd9'
        )
        return SimpleUploadedFile(name, jpeg_data, content_type="image/jpeg")

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
