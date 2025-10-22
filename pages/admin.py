from django.contrib import admin
from .models import HelpRequest


"""Admin registrations for the pages app.
"""

# Register your models here.


@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    """Admin configuration for managing support/help requests."""

    list_display = (
        'subject',
        'user',
        'priority',
        'status',
        'created_at',
        'updated_at',
    )
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('subject', 'message', 'name', 'email', 'user__username')
    autocomplete_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_open', 'mark_in_progress', 'mark_resolved']

    def mark_open(self, request, queryset):
        updated = queryset.update(status=HelpRequest.STATUS_OPEN)
        self.message_user(request, f"Marked {updated} request(s) as open.")

    mark_open.short_description = 'Mark selected requests as open'

    def mark_in_progress(self, request, queryset):
        updated = queryset.update(status=HelpRequest.STATUS_IN_PROGRESS)
        self.message_user(
            request, f"Marked {updated} request(s) as in progress.")

    mark_in_progress.short_description = 'Mark selected requests as in progress'

    def mark_resolved(self, request, queryset):
        updated = queryset.update(status=HelpRequest.STATUS_RESOLVED)
        self.message_user(request, f"Marked {updated} request(s) as resolved.")

    mark_resolved.short_description = 'Mark selected requests as resolved'
