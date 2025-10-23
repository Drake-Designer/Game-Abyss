from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify

try:
    from cloudinary.models import CloudinaryField
except ImportError:
    CloudinaryField = None

User = get_user_model()


class ApprovedManager(models.Manager):
    """Returns posts that are APPROVED (public on the site)."""

    def get_queryset(self):
        return super().get_queryset().filter(status=self.model.STATUS_APPROVED)


class CommentQuerySet(models.QuerySet):
    """Query helpers for comments."""

    def approved(self):
        return self.filter(status=self.model.STATUS_APPROVED)


class ApprovedCommentManager(models.Manager.from_queryset(CommentQuerySet)):
    """Returns comments that are approved for display."""

    def get_queryset(self):
        return super().get_queryset().approved()


class BlogPost(models.Model):
    """Blog post with moderation workflow and publishing metadata."""

    # Moderation workflow
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    title = models.CharField(max_length=100)
    slug = models.SlugField(
        max_length=120,
        unique_for_date='published_at',
        blank=True,
        editable=False,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_posts',
    )
    excerpt = models.CharField(max_length=250, blank=True)
    body = models.TextField()

    # Optional Cloudinary integration
    if CloudinaryField is not None:
        image = CloudinaryField('image', blank=True, null=True)
    else:
        image = models.ImageField(
            upload_to='blog_images/', blank=True, null=True)

    tags = models.CharField(
        max_length=100,
        blank=True,
        help_text='Comma-separated tags',
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    published_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    reading_time = models.PositiveIntegerField(
        default=1,
        help_text='Estimated reading time in minutes',
    )
    likes = models.PositiveIntegerField(default=0)
    rating = models.PositiveIntegerField(
        default=0,
        help_text='Rating out of 5 (future use)',
    )

    objects = models.Manager()
    approved = ApprovedManager()

    class Meta:
        ordering = ['-published_at', '-updated_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def save(self, *args, **kwargs):
        """Keep published_at in sync with status, generate slug, compute reading time, then save."""
        previous_status = None
        if self.pk:
            previous_status = BlogPost.objects.filter(
                pk=self.pk
            ).values_list('status', flat=True).first()

        # Publishing rules: approved posts get a timestamp; others do not surface.
        if self.status == self.STATUS_APPROVED and not self.published_at:
            self.published_at = timezone.now()
        elif self.status in (self.STATUS_PENDING, self.STATUS_REJECTED):
            self.published_at = None

        # Slug generation tied to reference date (published_at if present, otherwise now)
        if not self.slug:
            slug_field = self._meta.get_field('slug')
            base_slug = slugify(self.title)[:100] or 'post'
            reference_dt = self.published_at or timezone.now()
            date_str = reference_dt.strftime('%Y-%m-%d')
            base_without_suffix = f"{base_slug}-{date_str}"[
                : slug_field.max_length].rstrip('-')

            existing = BlogPost.objects.exclude(
                pk=self.pk) if self.pk else BlogPost.objects.all()
            if self.published_at:
                existing = existing.filter(
                    published_at__date=reference_dt.date())
            else:
                existing = existing.filter(published_at__isnull=True)

            unique_slug = base_without_suffix
            counter = 2
            while existing.filter(slug=unique_slug).exists():
                suffix = f"-{counter}"
                allowed_length = slug_field.max_length - len(suffix)
                trimmed_base = base_without_suffix[: max(
                    allowed_length, 1)].rstrip('-')
                if not trimmed_base:
                    trimmed_base = base_without_suffix[:1] or 'post'
                unique_slug = f"{trimmed_base}{suffix}"
                counter += 1

            self.slug = unique_slug

        # Reading time (~200 wpm)
        if self.body:
            words = len(self.body.split())
            self.reading_time = max(1, words // 200)

        super().save(*args, **kwargs)

        # Email: approved (copy fixed and themed)
        if (
            previous_status is not None
            and previous_status != self.STATUS_APPROVED
            and self.status == self.STATUS_APPROVED
            and self.author.email
        ):
            def _send_approved_email():
                send_mail(
                    subject=f"[Game-Abyss] Your post breached the front page",
                    message=(
                        "Explorer {username},\n\n"
                        "The Council has approved your post \"{title}\" and it now echoes across the Abyss, visible on the front page.\n"
                        "The Abyss has claimed your words as its own.\n\n"
                        "— Game-Abyss Council\n"
                    ).format(username=self.author.get_username(), title=self.title),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    recipient_list=[self.author.email],
                    fail_silently=True,
                )
            transaction.on_commit(_send_approved_email)

        # Email: rejected (copy corrected)
        if (
            previous_status is not None
            and previous_status != self.STATUS_REJECTED
            and self.status == self.STATUS_REJECTED
            and self.author.email
        ):
            def _send_rejected_email():
                send_mail(
                    subject=f"[Game-Abyss] Your post drifted back into the void",
                    message=(
                        "Explorer {username},\n\n"
                        "The Council has deemed your post \"{title}\" unworthy this round, so it will not be visible on the blog.\n"
                        "Re-forge your piece and resubmit when ready.\n\n"
                        "— Game-Abyss Council\n"
                    ).format(username=self.author.get_username(), title=self.title),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    recipient_list=[self.author.email],
                    fail_silently=True,
                )
            transaction.on_commit(_send_rejected_email)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Canonical URL like /blog/YYYY/MM/DD/slug/."""
        date = self.published_at or timezone.now()
        return f"/blog/{date.year}/{date.month:02d}/{date.day:02d}/{self.slug}/"


class Comment(models.Model):
    """User comment with simple moderation flags."""

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    body = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CommentQuerySet.as_manager()
    approved = ApprovedCommentManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"
