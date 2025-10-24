from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify

try:
    from cloudinary.models import CloudinaryField
except ImportError:
    CloudinaryField = None

# Email helpers (use on_commit)
from .emails import notify_author_post_approved, notify_author_post_rejected

User = get_user_model()


class ReactionType(models.TextChoices):
    LIKE = 'like', 'Like'
    LOVE = 'love', 'Love'
    DISLIKE = 'dislike', 'Dislike'


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
        previous_featured = None

        if self.pk:
            previous = BlogPost.objects.filter(
                pk=self.pk).values('status', 'featured').first()
            if previous:
                previous_status = previous['status']
                previous_featured = previous['featured']

        # Flag for signals: notify when featured flips from False -> True
        self._notify_featured = bool(
            previous_featured is not None and not previous_featured and self.featured
        )

        # Publishing rules
        if self.status == self.STATUS_APPROVED and not self.published_at:
            self.published_at = timezone.now()
        elif self.status in (self.STATUS_PENDING, self.STATUS_REJECTED):
            self.published_at = None

        # Slug
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

        # Email notifications via helpers (after commit)
        if (
            previous_status is not None
            and previous_status != self.STATUS_APPROVED
            and self.status == self.STATUS_APPROVED
        ):
            transaction.on_commit(lambda: notify_author_post_approved(self))

        if (
            previous_status is not None
            and previous_status != self.STATUS_REJECTED
            and self.status == self.STATUS_REJECTED
        ):
            transaction.on_commit(lambda: notify_author_post_rejected(self))

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


class PostReaction(models.Model):
    """A reaction (like, love, dislike) from a user on a post."""
    post = models.ForeignKey(
        'BlogPost', on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='post_reactions')
    reaction = models.CharField(max_length=16, choices=ReactionType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Post Reaction"
        verbose_name_plural = "Post Reactions"
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'user'], name='unique_post_reaction_per_user')
        ]

    def __str__(self):
        return f"{self.user} reacted {self.reaction} to {self.post}"


class CommentReaction(models.Model):
    """A reaction (like, love, dislike) from a user on a comment."""
    comment = models.ForeignKey(
        'Comment', on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comment_reactions')
    reaction = models.CharField(max_length=16, choices=ReactionType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Comment Reaction"
        verbose_name_plural = "Comment Reactions"
        constraints = [
            models.UniqueConstraint(
                fields=['comment', 'user'], name='unique_comment_reaction_per_user')
        ]

    def __str__(self):
        return f"{self.user} reacted {self.reaction} to comment {self.comment_id}"


class CommentReport(models.Model):
    """A report filed by a user against a comment."""

    class Reason(models.TextChoices):
        INAPPROPRIATE = 'inappropriate', 'Inappropriate'
        SPAM = 'spam', 'Spam'

    comment = models.ForeignKey(
        'Comment', on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comment_reports')
    reason = models.CharField(max_length=32, choices=Reason.choices)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Comment Report"
        verbose_name_plural = "Comment Reports"
        constraints = [
            models.UniqueConstraint(
                fields=['comment', 'reported_by'], name='unique_comment_report_per_user'
            )
        ]

    def __str__(self):
        return f"Report on comment {self.comment_id} by {self.reported_by}"
