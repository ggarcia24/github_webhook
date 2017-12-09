from django.contrib import admin

from .models import WebhookTransaction, RepositoryFilePattern, PullRequestTransactionResult, FilePatternPermissions


class RepositoryFilePatternAdmin(admin.ModelAdmin):
    list_display = ['name', 'pattern', 'description']


class PullRequestTransactionResultAdmin(admin.ModelAdmin):
    list_display = ['date_processed', 'action', 'number', 'repository', 'permission_violation']


admin.site.register(WebhookTransaction)
admin.site.register(PullRequestTransactionResult, PullRequestTransactionResultAdmin)
admin.site.register(RepositoryFilePattern, RepositoryFilePatternAdmin)
admin.site.register(FilePatternPermissions)

# Register your models here.
