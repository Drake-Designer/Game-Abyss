# blog/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .forms import BlogPostForm
from .models import (
    BlogPost,
    Comment,
    CommentReaction,
    CommentReport,
    PostReaction,
)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    """Moderation console for BlogPost - quick actions to approve, reject, and feature."""
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

    actions = ['mark_pending', 'mark_approved', 'mark_rejected',
               'mark_featured', 'mark_unfeatured']
    form = BlogPostForm

    def save_model(self, request, obj, form, change):
        """Force author to be operator; assign default status depending on role."""
        obj.author = request.user
        if not change:
            if request.user.is_staff:
                obj.status = BlogPost.STATUS_APPROVED
            else:
                obj.status = BlogPost.STATUS_PENDING
        super().save_model(request, obj, form, change)

    def thumbnail(self, obj):
        """Small preview thumbnail for posts."""
        if getattr(obj, 'image', None):
            return format_html('<img src="{}" style="height:40px;border-radius:4px;"/>', obj.image.url)
        return '-'
    thumbnail.short_description = 'Image'

    def view_on_site(self, obj):
        """Open the post directly on the site."""
        return format_html('<a href="{}" target="_blank">View</a>', obj.get_absolute_url())
    view_on_site.short_description = 'On site'

    list_display = ('thumbnail',) + list_display + ('view_on_site',)

    def get_readonly_fields(self, request, obj=None):
        """Status is editable only for staff or superusers."""
        ro = list(self.readonly_fields)
        if not (request.user.is_staff or request.user.is_superuser):
            ro.extend(['status'])
        return ro

    def get_prepopulated_fields(self, request, obj=None):
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
        """Only superusers can erase content from the Abyss."""
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.has_perm('blog.change_blogpost'):
            for action in list(actions):
                actions.pop(action)
        return actions

    # Moderation actions
    def mark_pending(self, request, queryset):
        updated = 0
        for post in queryset:
            post.status = BlogPost.STATUS_PENDING
            post.save()
            updated += 1
        self.message_user(
            request, f"Shifted {updated} post(s) back into stasis (Pending).")
    mark_pending.short_description = 'Mark selected posts as pending'

    def mark_approved(self, request, queryset):
        updated = 0
        for post in queryset:
            post.status = BlogPost.STATUS_APPROVED
            post.save()
            updated += 1
        self.message_user(
            request, f"Raised {updated} post(s) to the front page (Approved).")
    mark_approved.short_description = 'Approve selected posts'

    def mark_rejected(self, request, queryset):
        updated = 0
        for post in queryset:
            post.status = BlogPost.STATUS_REJECTED
            post.save()
            updated += 1
        self.message_user(
            request, f"Cast {updated} post(s) into the void (Rejected).")
    mark_rejected.short_description = 'Reject selected posts'

    # Featured flags
    def mark_featured(self, request, queryset):
        updated = 0
        for post in queryset:
            if not post.featured:
                post.featured = True
                post.save(update_fields=['featured'])
                updated += 1
        self.message_user(request, f"Marked {updated} post(s) as Featured ⭐")
    mark_featured.short_description = 'Mark selected posts as featured'

    def mark_unfeatured(self, request, queryset):
        updated = 0
        for post in queryset:
            if post.featured:
                post.featured = False
                post.save(update_fields=['featured'])
                updated += 1
        self.message_user(
            request, f"Removed Featured mark from {updated} post(s).")
    mark_unfeatured.short_description = 'Remove featured flag'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Moderation console for comments."""
    list_display = ('post', 'author', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'post')
    search_fields = ('post__title', 'author__username', 'body')
    autocomplete_fields = ('post', 'author')
    actions = ['mark_pending', 'mark_approved', 'mark_rejected']

    def mark_pending(self, request, queryset):
        updated = queryset.update(status=Comment.STATUS_PENDING)
        self.message_user(
            request, f"Queued {updated} comment(s) in stasis (Pending).")
    mark_pending.short_description = 'Mark selected comments as pending'

    def mark_approved(self, request, queryset):
        updated = queryset.update(status=Comment.STATUS_APPROVED)
        self.message_user(
            request, f"Cleared {updated} comment(s) for orbit (Approved).")
    mark_approved.short_description = 'Mark selected comments as approved'

    def mark_rejected(self, request, queryset):
        updated = queryset.update(status=Comment.STATUS_REJECTED)
        self.message_user(
            request, f"Cast {updated} comment(s) into the void (Rejected).")
    mark_rejected.short_description = 'Mark selected comments as rejected'


@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'reaction', 'created_at')
    list_filter = ('reaction', 'created_at')
    search_fields = ('post__title', 'user__username')


@admin.register(CommentReaction)
class CommentReactionAdmin(admin.ModelAdmin):
    list_display = ('comment', 'user', 'reaction', 'created_at')
    list_filter = ('reaction', 'created_at')
    search_fields = ('comment__post__title', 'user__username')


@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    list_display = ('comment', 'reported_by',
                    'reason', 'resolved', 'created_at')
    list_filter = ('reason', 'resolved', 'created_at')
    search_fields = (
        'comment__body',
        'comment__post__title',
        'reported_by__username',
    )
    readonly_fields = ('comment', 'reported_by', 'notes', 'created_at')
    actions = ['mark_resolved']

    def mark_resolved(self, request, queryset):
        updated = queryset.update(resolved=True)
        self.message_user(request, f"Marked {updated} report(s) as resolved.")
    mark_resolved.short_description = 'Mark reports as resolved'
