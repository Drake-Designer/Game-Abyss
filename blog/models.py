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
    """Manager returning posts that are published and visible on the blog."""

    def get_queryset(self):
        return super().get_queryset().filter(status=self.model.STATUS_PUBLISHED)


class CommentQuerySet(models.QuerySet):
    """QuerySet helpers used across comment views."""

    def approved(self):
        return self.filter(status=self.model.STATUS_APPROVED)


class ApprovedCommentManager(models.Manager.from_queryset(CommentQuerySet)):
    """Manager returning comments that are approved for display."""

    def get_queryset(self):
        return super().get_queryset().approved()


class BlogPost(models.Model):
    """A blog post record with workflow, flags and useful metadata."""

    # Workflow
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    # Backward compatibility aliases for legacy code
    STATUS_APPROVED = STATUS_PUBLISHED
    STATUS_REJECTED = STATUS_DRAFT

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
        default=STATUS_DRAFT,
    )
    featured = models.BooleanField(default=False)

    # Use default=timezone.now instead of auto_now_add to avoid conflicts on existing rows
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
        """Generate slug, sync published_at with status, compute reading time, then save."""
        previous_status = None
        if self.pk:
            previous_status = BlogPost.objects.filter(
                pk=self.pk
            ).values_list('status', flat=True).first()

        # Sync published_at with workflow
        if self.status == self.STATUS_PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        elif self.status == self.STATUS_DRAFT:
            self.published_at = None

        # Auto slug from title and reference date when missing
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

        # Reading time at ~200 wpm
        if self.body:
            words = len(self.body.split())
            self.reading_time = max(1, words // 200)

        super().save(*args, **kwargs)

        # Optional notification when a post is moved to draft from another state
        if (
            previous_status is not None
            and previous_status != self.STATUS_DRAFT
            and self.status == self.STATUS_DRAFT
            and self.author.email
        ):
            def _send_rejection_email():
                send_mail(
                    subject=f"Il tuo post '{self.title}' non è stato approvato",
                    message=(
                        "Ciao {username},\n\n"
                        "il tuo post non è stato approvato dalla redazione e non sarà visibile sul blog.\n"
                        "Puoi aggiornarlo e riproporlo per la revisione in qualsiasi momento.\n\n"
                        "Grazie per aver contribuito a Game Abyss!"
                    ).format(username=self.author.get_username()),
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    recipient_list=[self.author.email],
                    fail_silently=True,
                )
            transaction.on_commit(_send_rejection_email)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Canonical URL like /blog/YYYY/MM/DD/slug/."""
        date = self.published_at or timezone.now()
        return f"/blog/{date.year}/{date.month:02d}/{date.day:02d}/{self.slug}/"


class Comment(models.Model):
    """A comment left by a user on a blog post."""

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

    # Same approach as BlogPost to avoid mutually exclusive options
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
