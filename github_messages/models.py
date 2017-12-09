from django.db import models
from django.utils import timezone


class WebhookTransaction(models.Model):
    UNPROCESSED = 1
    PROCESSED = 2
    ERROR = 3

    STATUSES = (
        (UNPROCESSED, 'Unprocessed'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    )

    date_generated = models.DateTimeField()
    date_received = models.DateTimeField(default=timezone.now)
    body = models.TextField()
    request_meta = models.TextField()
    status = models.CharField(max_length=250, choices=STATUSES, default=UNPROCESSED)

    def __str__(self):  # __unicode__ on Python 2
        return self.date_generated.isoformat()


class FilePatternPermissions(models.Model):
    USER = 1
    TEAM = 2

    OBJECT_TYPES = (
        (USER, 'User'),
        (TEAM, 'Team')
    )
    name = models.CharField(max_length=250)
    object_type = models.IntegerField(choices=OBJECT_TYPES, default=USER)

    def __str__(self):
        return self.name + ' ({})'.format(self.get_object_type_display())


class RepositoryFilePattern(models.Model):
    name = models.CharField(max_length=250)
    pattern = models.CharField(max_length=250)
    description = models.TextField()
    authorized = models.ManyToManyField(FilePatternPermissions)

    def __str__(self):
        return self.name


class PullRequestTransactionResult(models.Model):
    date_processed = models.DateTimeField(default=timezone.now)
    webhook_transaction = models.OneToOneField(WebhookTransaction, on_delete=models.CASCADE)

    action = models.CharField(max_length=250)
    number = models.IntegerField()
    owner = models.CharField(max_length=250)
    sender = models.CharField(max_length=250)
    repository = models.CharField(max_length=250)
    changed_files = models.TextField()
    permission_violation = models.BooleanField()
