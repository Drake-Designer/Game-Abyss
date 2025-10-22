from django.contrib import admin
from django.utils.html import format_html

from .forms import BlogPostForm
from .models import BlogPost, Comment


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Admin interface for BlogPost.

    Shows a thumbnail, status, featured flag, and quick actions to publish or move back to draft.
    """
    list_display = (
        'title',
        'author',
        'status',
        'featured',
        'published_at',
        'updated_at',
    )
    list_filter = ('status', 'author', 'published_at', 'featured')
    search_fields = ('title', 'body', 'excerpt', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = (
        'reading_time',
        'likes',
        'rating',
        'slug',
        'published_at',
        'updated_at',
        'author',
    )
    date_hierarchy = 'published_at'
    ordering = ('-published_at',)

    actions = ['mark_published', 'mark_draft',
               'mark_featured', 'mark_unfeatured']
    form = BlogPostForm

    def save_model(self, request, obj, form, change):
        """Assign the author to the current user before saving."""
        obj.author = request.user
        super().save_model(request, obj, form, change)

    def thumbnail(self, obj):
        """Return a small thumbnail HTML for list display or '-' if none."""
        if getattr(obj, 'image', None):
            return format_html(
                '<img src="{}" style="height:40px;border-radius:4px;"/>',
                obj.image.url,
            )
        return '-'
    thumbnail.short_description = 'Image'

    def view_on_site(self, obj):
        """Return a short link that opens the post on the site."""
        url = obj.get_absolute_url()
        return format_html('<a href="{}" target="_blank">View</a>', url)
    view_on_site.short_description = 'On site'

    # Place thumbnail first and an on-site link last
    list_display = ('thumbnail',) + list_display + ('view_on_site',)

    def get_readonly_fields(self, request, obj=None):
        """Make some fields read-only for non-superusers."""
        ro = list(self.readonly_fields)
        if not request.user.is_superuser:
            ro.extend(['status'])
        return ro

    def get_prepopulated_fields(self, request, obj=None):
        """Return only prepopulated fields that actually exist on the form."""
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
        if not request.user.has_perm('blog.change_blogpost'):
            # Remove all bulk actions for users without change permissions
            for action in list(actions):
                actions.pop(action)
        return actions

    def mark_published(self, request, queryset):
        """Admin action: mark selected posts as published."""
        updated = 0
        for post in queryset:
            post.status = BlogPost.STATUS_PUBLISHED
            post.save()
            updated += 1
        self.message_user(request, f"Marked {updated} post(s) as published.")
    mark_published.short_description = 'Publish selected posts'

    def mark_draft(self, request, queryset):
        """Admin action: move selected posts back to draft."""
        updated = 0
        for post in queryset:
            post.status = BlogPost.STATUS_DRAFT
            post.save()
            updated += 1
        self.message_user(request, f"Moved {updated} post(s) to draft.")
    mark_draft.short_description = 'Move selected posts to draft'

    def mark_featured(self, request, queryset):
        """Admin action: set featured flag on selected posts."""
        updated = queryset.update(featured=True)
        self.message_user(request, f"Marked {updated} post(s) as featured.")
    mark_featured.short_description = 'Mark selected posts as featured'

    def mark_unfeatured(self, request, queryset):
        """Admin action: remove featured flag from selected posts."""
        updated = queryset.update(featured=False)
        self.message_user(
            request, f"Removed featured flag from {updated} post(s).")
    mark_unfeatured.short_description = 'Remove featured flag'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for moderating blog comments."""
    list_display = ('post', 'author', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'post')
    search_fields = ('post__title', 'author__username', 'body')
    autocomplete_fields = ('post', 'author')
    actions = ['mark_pending', 'mark_approved', 'mark_rejected']

    def mark_pending(self, request, queryset):
        updated = queryset.update(status=Comment.STATUS_PENDING)
        self.message_user(request, f"Marked {updated} comment(s) as pending.")
    mark_pending.short_description = 'Mark selected comments as pending'

    def mark_approved(self, request, queryset):
        updated = queryset.update(status=Comment.STATUS_APPROVED)
        self.message_user(request, f"Marked {updated} comment(s) as approved.")
    mark_approved.short_description = 'Mark selected comments as approved'

    def mark_rejected(self, request, queryset):
        updated = queryset.update(status=Comment.STATUS_REJECTED)
        self.message_user(request, f"Marked {updated} comment(s) as rejected.")
    mark_rejected.short_description = 'Mark selected comments as rejected'
