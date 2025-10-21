from django.contrib import admin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'published_at', 'updated_at')
    list_filter = ('status', 'author', 'published_at')
    search_fields = ('title', 'body', 'excerpt', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('reading_time', 'likes', 'rating',
                       'slug', 'published_at', 'updated_at')
    date_hierarchy = 'published_at'
    ordering = ('-published_at',)

    def get_readonly_fields(self, request, obj=None):
        # Only superusers/staff can change status
        ro = list(self.readonly_fields)
        if not request.user.is_superuser and not request.user.is_staff:
            ro.append('status')
        return ro
