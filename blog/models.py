# /* ============================================================
#    *** BLOG: Models ***
#    ============================================================ */
"""Define blog data models."""

# /* ============================================================
#    *** BLOG: Models: Imports ***
#    ============================================================ */
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify

try:
    from cloudinary.models import CloudinaryField
except ImportError:  # pragma: no cover
    CloudinaryField = None  # type: ignore

# Email helpers
from .emails import notify_author_post_approved, notify_author_post_rejected

User = get_user_model()


# /* ============================================================
#    *** BLOG: Models: Choices and Managers ***
#    ============================================================ */
class ReactionType(models.TextChoices):  # pylint: disable=too-many-ancestors
    """List possible reaction types."""
    LIKE = "like", "Like"
    LOVE = "love", "Love"
    DISLIKE = "dislike", "Dislike"


class ApprovedManager(models.Manager):  # pylint: disable=too-few-public-methods
    """Provide manager for approved posts."""

    def get_queryset(self):
        """Return queryset filtered to approved posts."""
        return super().get_queryset().filter(status=self.model.STATUS_APPROVED)


class CommentQuerySet(models.QuerySet):  # pylint: disable=too-few-public-methods
    """Offer comment queryset helpers."""

    def approved(self):
        """Return comments flagged as approved."""
        return self.filter(status=self.model.STATUS_APPROVED)


class ApprovedCommentManager(  # pylint: disable=too-few-public-methods
    models.Manager.from_queryset(CommentQuerySet)
):
    """Provide manager for approved comments."""

    def get_queryset(self):
        """Return queryset filtered to approved comments."""
        return super().get_queryset().approved()


# /* ============================================================
#    *** BLOG: Models: Tag Utilities ***
#    ============================================================ */
def _parse_tag_string(raw_value: str) -> list[dict]:
    """Parse raw tag text into unique tag dictionaries."""
    tags: list[dict] = []
    seen_slugs: set[str] = set()
    for fragment in (raw_value or "").split(","):
        name = fragment.strip()
        if not name:
            continue
        slug_val = slugify(name)
        if not slug_val or slug_val in seen_slugs:
            continue
        seen_slugs.add(slug_val)
        tags.append({"name": name, "slug": slug_val})
    return tags


def _normalize_tag_string(raw_value: str) -> str:
    """Normalize tag text into a cleaned comma list."""
    return ", ".join(tag["name"] for tag in _parse_tag_string(raw_value))


# /* ============================================================
#    *** BLOG: Models: Core Models ***
#    ============================================================ */
class BlogPost(models.Model):  # pylint: disable=too-many-ancestors
    """Represent a blog post with moderation metadata."""

    # Moderation workflow
    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    title = models.CharField(max_length=100)
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        editable=False,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="blog_posts",
    )
    excerpt = models.CharField(max_length=250, blank=True)
    body = models.TextField()

    # Optional Cloudinary integration
    if CloudinaryField is not None:
        image = CloudinaryField("image", blank=True, null=True)
    else:
        image = models.ImageField(  # type: ignore[assignment]
            upload_to="blog_images/", blank=True, null=True
        )

    tags = models.CharField(
        max_length=100,
        blank=True,
        help_text="Comma-separated tags",
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
        help_text="Estimated reading time in minutes",
    )
    likes = models.PositiveIntegerField(default=0)
    rating = models.PositiveIntegerField(
        default=0,
        help_text="Rating out of 5 (future use)",
    )

    objects = models.Manager()
    approved = ApprovedManager()

    class Meta:
        """Configure blog post metadata."""
        ordering = ["-published_at", "-updated_at"]
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"

    def save(self, *args, **kwargs):  # pylint: disable=too-many-locals
        """Persist post while maintaining derived fields."""
        previous_status = None
        previous_featured = None

        if self.pk:
            previous = (
                BlogPost.objects.filter(pk=self.pk)
                .values("status", "featured")
                .first()
            )
            if previous:
                previous_status = previous["status"]
                previous_featured = previous["featured"]

        # Flag for signals: notify when featured flips from False to True
        self._notify_featured = bool(  # pylint: disable=attribute-defined-outside-init
            previous_featured is not None
            and not previous_featured
            and self.featured
        )

        # Publishing rules
        if self.status == self.STATUS_APPROVED and not self.published_at:
            self.published_at = timezone.now()
        elif self.status in (
            self.STATUS_PENDING,
            self.STATUS_REJECTED,
            self.STATUS_DRAFT,
        ):
            self.published_at = None

        # Slug
        if not self.slug:
            slug_field = self._meta.get_field("slug")  # Django provides _meta
            base_slug = slugify(self.title)[: slug_field.max_length] or "post"
            base_without_suffix = base_slug.rstrip("-") or "post"

            existing = (
                BlogPost.objects.exclude(pk=self.pk)
                if self.pk
                else BlogPost.objects.all()
            )

            unique_slug = base_without_suffix
            counter = 2
            while existing.filter(slug=unique_slug).exists():
                suffix = f"-{counter}"
                allowed_length = slug_field.max_length - len(suffix)
                trimmed_base = base_without_suffix[: max(
                    allowed_length, 1)].rstrip("-")
                if not trimmed_base:
                    trimmed_base = base_without_suffix[:1] or "post"
                unique_slug = f"{trimmed_base}{suffix}"
                counter += 1

            self.slug = unique_slug

        # Tags (normalize/clean duplicates)
        self.tags = _normalize_tag_string(self.tags) if self.tags else ""

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

    def __str__(self) -> str:
        """Return readable post title."""
        return self.title

    @property
    def tag_list(self) -> list[dict]:
        """Return parsed representation of tags."""
        return _parse_tag_string(self.tags)

    @staticmethod
    def normalize_tags(value: str) -> str:
        """Normalize provided tag text."""
        return _normalize_tag_string(value)

    def get_absolute_url(self) -> str:
        """Build canonical URL for the post."""
        date = self.published_at or self.created_at or timezone.now()
        return (
            f"/blog/{date.year}/{date.month:02d}/{date.day:02d}/"
            f"{self.slug}/"
        )


class Comment(models.Model):  # pylint: disable=too-many-ancestors
    """Represent a user comment with moderation flags."""

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
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
        """Configure comment metadata."""
        ordering = ["-created_at"]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self) -> str:
        """Return readable comment label."""
        return f"Comment by {self.author} on {self.post}"


class PostReaction(models.Model):  # pylint: disable=too-many-ancestors
    """Record a user reaction on a post."""
    post = models.ForeignKey(
        "BlogPost", on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="post_reactions"
    )
    reaction = models.CharField(max_length=16, choices=ReactionType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Configure post reaction metadata."""
        verbose_name = "Post Reaction"
        verbose_name_plural = "Post Reactions"
        constraints = [
            models.UniqueConstraint(
                fields=["post", "user"], name="unique_post_reaction_per_user"
            )
        ]

    def __str__(self) -> str:
        """Return readable post reaction label."""
        return f"{self.user} reacted {self.reaction} to {self.post}"


class CommentReaction(models.Model):  # pylint: disable=too-many-ancestors
    """Record a user reaction on a comment."""
    comment = models.ForeignKey(
        "Comment", on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_reactions"
    )
    reaction = models.CharField(max_length=16, choices=ReactionType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Configure comment reaction metadata."""
        verbose_name = "Comment Reaction"
        verbose_name_plural = "Comment Reactions"
        constraints = [
            models.UniqueConstraint(
                fields=["comment", "user"],
                name="unique_comment_reaction_per_user",
            )
        ]

    def __str__(self) -> str:
        """Return readable comment reaction label."""
        return f"{self.user} reacted {self.reaction} to comment {self.comment.pk}"


class CommentReport(models.Model):  # pylint: disable=too-many-ancestors
    """Store a user report against a comment."""

    class Reason(models.TextChoices):  # pylint: disable=too-many-ancestors
        """List comment report reasons."""
        INAPPROPRIATE = "inappropriate", "Inappropriate"
        SPAM = "spam", "Spam"

    comment = models.ForeignKey(
        "Comment", on_delete=models.CASCADE, related_name="reports"
    )
    reported_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_reports"
    )
    reason = models.CharField(max_length=32, choices=Reason.choices)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    class Meta:
        """Configure comment report metadata."""
        verbose_name = "Comment Report"
        verbose_name_plural = "Comment Reports"
        constraints = [
            models.UniqueConstraint(
                fields=["comment", "reported_by"],
                name="unique_comment_report_per_user",
            )
        ]

    def __str__(self) -> str:
        """Return readable comment report label."""
        return f"Report on comment {self.comment.pk} by {self.reported_by}"


class ModerationActionLog(models.Model):  # pylint: disable=too-many-ancestors
    """Store a moderation action audit entry."""

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderation_logs",
    )
    action = models.CharField(max_length=50)
    target_model = models.CharField(max_length=100)
    target_id = models.PositiveIntegerField()
    target_repr = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Explicit manager to satisfy static analysis
    objects = models.Manager()

    class Meta:
        """Configure moderation action log metadata."""
        ordering = ["-created_at"]
        verbose_name = "Moderation action"
        verbose_name_plural = "Moderation actions"

    def __str__(self) -> str:
        """Return readable moderation log label."""
        if self.actor and hasattr(self.actor, "get_username"):
            actor_label = self.actor.get_username()
        elif self.actor:
            actor_label = str(self.actor)
        else:
            actor_label = "System"
        return f"{self.action} by {actor_label} on {self.target_model}#{self.target_id}"


def log_moderation_action(actor, action: str, target, notes: str = "") -> None:
    """Create a moderation audit entry."""
    target_model = target.__class__.__name__
    target_id = getattr(target, "pk", 0) or 0
    target_repr = str(target)
    actor_value = actor if getattr(actor, "is_authenticated", False) else None

    ModerationActionLog.objects.create(
        actor=actor_value,
        action=action,
        target_model=target_model,
        target_id=target_id,
        target_repr=target_repr[:255],
        notes=notes,
    )
