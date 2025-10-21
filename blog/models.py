from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify

try:  # pragma: no cover - optional dependency
    from cloudinary.models import CloudinaryField
except ImportError:  # pragma: no cover - fallback for local development/tests
    CloudinaryField = None

User = get_user_model()


class ApprovedManager(models.Manager):
    """Manager returning posts that are approved and visible on the blog."""

    def get_queryset(self):
        return super().get_queryset().filter(status=self.model.STATUS_APPROVED)


class BlogPost(models.Model):
    """A blog post record.

    Stores title, author, body, image, tags, status and timestamps
    """
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    title = models.CharField(max_length=100)
    slug = models.SlugField(
        max_length=120, unique_for_date='published_at', blank=True, editable=False)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='blog_posts')
    excerpt = models.CharField(max_length=250, blank=True)
    body = models.TextField()
    if CloudinaryField is not None:
        image = CloudinaryField('image', blank=True, null=True)
    else:
        image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    tags = models.CharField(max_length=100, blank=True,
                            help_text='Comma-separated tags')
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_REJECTED)
    published_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    reading_time = models.PositiveIntegerField(
        default=1, help_text='Estimated reading time in minutes')
    likes = models.PositiveIntegerField(default=0)
    rating = models.PositiveIntegerField(
        default=0, help_text='Rating out of 5 (future use)')

    objects = models.Manager()
    approved = ApprovedManager()

    class Meta:
        ordering = ['-published_at', '-updated_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def save(self, *args, **kwargs):
        """Auto-generate slug and compute reading time, then save.

        If `slug` is empty it is created from the title and published date.
        Reading time is estimated from the body text.
        """
        previous_status = None
        if self.pk:
            previous_status = BlogPost.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        should_notify_rejection = (
            previous_status is not None
            and previous_status != self.STATUS_REJECTED
            and self.status == self.STATUS_REJECTED
        )

        if self.status == self.STATUS_APPROVED and not self.published_at:
            self.published_at = timezone.now()
        elif self.status == self.STATUS_REJECTED:
            self.published_at = None

        # Auto-generate slug from title if not set
        if not self.slug:
            base_slug = slugify(self.title)[:100]
            date_str = self.published_at.strftime(
                '%Y-%m-%d') if self.published_at else timezone.now().strftime('%Y-%m-%d')
            self.slug = f"{base_slug}-{date_str}"
        # Calculate reading time (roughly 200 words/minute)
        if self.body:
            words = len(self.body.split())
            self.reading_time = max(1, words // 200)
        super().save(*args, **kwargs)

        if should_notify_rejection and self.author.email:
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
        """Return the canonical URL for this post.

        Example: /blog/2025/10/21/my-post-slug/
        """
        date = self.published_at or timezone.now()
        return f"/blog/{date.year}/{date.month:02d}/{date.day:02d}/{self.slug}/"
