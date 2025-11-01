# ============================================================
#   *** GALLERY: Tests ***
# ============================================================

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
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
