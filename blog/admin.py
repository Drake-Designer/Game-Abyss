from django.contrib import admin
from .models import BlogPost
from .forms import BlogPostForm
from django.utils.html import format_html
from django.urls import reverse


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Admin interface for BlogPost.

    Shows a thumbnail, status, and handy actions to publish/unpublish posts.
    """
    list_display = ('title', 'author', 'status', 'published_at', 'updated_at')
    list_filter = ('status', 'author', 'published_at')
    search_fields = ('title', 'body', 'excerpt', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('reading_time', 'likes', 'rating',
                       'slug', 'published_at', 'updated_at')
    date_hierarchy = 'published_at'
    ordering = ('-published_at',)

    actions = ['make_published', 'make_draft']
    form = BlogPostForm

    def thumbnail(self, obj):
        """Return a small thumbnail HTML for list display (or '-' if none)."""
        if obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;"/>', obj.image.url)
        return '-'

    thumbnail.short_description = 'Image'

    def view_on_site(self, obj):
        """Return a short 'View' link that opens the post on the site."""
        url = obj.get_absolute_url()
        return format_html('<a href="{}" target="_blank">View</a>', url)

    view_on_site.short_description = 'On site'

    list_display = ('thumbnail',) + list_display + ('view_on_site',)

    def get_readonly_fields(self, request, obj=None):
        """Make some fields read-only for non-staff users.

        Regular users cannot change the post status.
        """
        ro = list(self.readonly_fields)
        if not request.user.is_superuser and not request.user.is_staff:
            ro.append('status')
        return ro

    def get_prepopulated_fields(self, request, obj=None):
        """Return only the prepopulated_fields that actually exist on the form.

        This avoids KeyError when a form (or a custom form) does not expose
        a field that `prepopulated_fields` references.
        """
        fields = getattr(self, 'prepopulated_fields', {}) or {}
        try:
            form = self.get_form(request, obj)()
        except Exception:
            return {}

        safe = {}
        for key, deps in fields.items():
            if key in form.fields and all(d in form.fields for d in deps):
                safe[key] = deps
        return safe

    def make_published(self, request, queryset):
        """Admin action: mark selected posts as published."""
        updated = queryset.update(status='published')
        self.message_user(request, f"Marked {updated} post(s) as published.")

    make_published.short_description = 'Mark selected posts as published'

    def make_draft(self, request, queryset):
        """Admin action: mark selected posts as draft."""
        updated = queryset.update(status='draft')
        self.message_user(request, f"Marked {updated} post(s) as draft.")

    make_draft.short_description = 'Mark selected posts as draft'
