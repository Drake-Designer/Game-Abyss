from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone

User = get_user_model()


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=100)
    slug = models.SlugField(
        max_length=120, unique_for_date='published_at', blank=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='blog_posts')
    excerpt = models.CharField(max_length=250, blank=True)
    body = models.TextField()
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    tags = models.CharField(max_length=100, blank=True,
                            help_text='Comma-separated tags')
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    reading_time = models.PositiveIntegerField(
        default=1, help_text='Estimated reading time in minutes')
    likes = models.PositiveIntegerField(default=0)
    rating = models.PositiveIntegerField(
        default=0, help_text='Rating out of 5 (future use)')

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def save(self, *args, **kwargs):
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
