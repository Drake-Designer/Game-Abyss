from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone

User = get_user_model()


class PublishedManager(models.Manager):
    """Manager returning posts that are published and approved."""

    def get_queryset(self):
        return super().get_queryset().filter(status='published', is_approved=True)


class BlogPost(models.Model):
    """A blog post record.

    Stores title, author, body, image, tags, status and timestamps
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=100)
    slug = models.SlugField(
        max_length=120, unique_for_date='published_at', blank=True, editable=False)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='blog_posts')
    excerpt = models.CharField(max_length=250, blank=True)
    body = models.TextField()
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    tags = models.CharField(max_length=100, blank=True,
                            help_text='Comma-separated tags')
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft')
    is_approved = models.BooleanField(
        default=False,
        help_text='Indicates whether the post has passed editorial review.')
    published_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    reading_time = models.PositiveIntegerField(
        default=1, help_text='Estimated reading time in minutes')
    likes = models.PositiveIntegerField(default=0)
    rating = models.PositiveIntegerField(
        default=0, help_text='Rating out of 5 (future use)')

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def save(self, *args, **kwargs):
        """Auto-generate slug and compute reading time, then save.

        If `slug` is empty it is created from the title and published date.
        Reading time is estimated from the body text.
        """
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

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Return the canonical URL for this post.

        Example: /blog/2025/10/21/my-post-slug/
        """
        date = self.published_at or timezone.now()
        return f"/blog/{date.year}/{date.month:02d}/{date.day:02d}/{self.slug}/"
