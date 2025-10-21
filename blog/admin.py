from django.contrib import admin
from django.utils.html import format_html

from .forms import BlogPostForm
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Admin interface for BlogPost.

    Shows a thumbnail, status, and handy actions to publish/unpublish posts.
    """
    list_display = ('title', 'author', 'status',
                    'published_at', 'updated_at')
    list_filter = ('status', 'author', 'published_at')
    search_fields = ('title', 'body', 'excerpt', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('reading_time', 'likes', 'rating',
                       'slug', 'published_at', 'updated_at', 'author')
    date_hierarchy = 'published_at'
    ordering = ('-published_at',)

    actions = ['mark_approved', 'mark_rejected']
    form = BlogPostForm

    def save_model(self, request, obj, form, change):
        """Assign the author to the current user before saving."""
        obj.author = request.user
        super().save_model(request, obj, form, change)

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
        if not request.user.is_superuser:
            ro.extend(['status'])
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

    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for superusers."""
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            # Remove all bulk actions for non-superusers
            for action in list(actions):
                actions.pop(action)
        return actions

    def mark_approved(self, request, queryset):
        """Admin action: mark selected posts as approved."""
        updated = 0
        for post in queryset:
            post.status = BlogPost.STATUS_APPROVED
            post.save()
            updated += 1
        self.message_user(request, f"Marked {updated} post(s) as approved.")

    mark_approved.short_description = 'Mark selected posts as approved'

    def mark_rejected(self, request, queryset):
        """Admin action: mark selected posts as rejected."""
        updated = 0
        for post in queryset:
            post.status = BlogPost.STATUS_REJECTED
            post.save()
            updated += 1
        self.message_user(request, f"Marked {updated} post(s) as rejected.")

    mark_rejected.short_description = 'Mark selected posts as rejected'
