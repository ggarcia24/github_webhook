import fnmatch
import json

from celery.schedules import crontab
from celery.task import PeriodicTask
from celery.utils.log import get_task_logger
from django.conf import settings
from github import Github, UnknownObjectException

from .models import WebhookTransaction, PullRequestTransactionResult, RepositoryFilePattern

_github_client = Github(login_or_token=settings.GITHUB_TOKEN)


class UserNotAllowedException(Exception):
    pass


class ProcessMessages(PeriodicTask):
    run_every = crontab()  # this will run once a minute
    logger = get_task_logger(__name__)

    def run(self, **kwargs):
        # Obtain all the transactions from the DB
        unprocessed_trans = self.get_transactions_to_process()

        for trans in unprocessed_trans:
            try:
                self.process_trans(trans)
                trans.status = WebhookTransaction.PROCESSED
                trans.save()
            except Exception as e:
                self.logger.error(str(e))
                trans.status = WebhookTransaction.ERROR
                trans.save()

    @staticmethod
    def get_transactions_to_process():
        return WebhookTransaction.objects.filter(
            status=WebhookTransaction.UNPROCESSED
        )

    def process_trans(self, transaction):

        # Here we should do the magic
        # Obtain the json from the request
        body = transaction.body
        pr_info = json.loads(body)
        action = pr_info['action']
        pr_number = pr_info['number']
        pr_owner = pr_info['pull_request']['user']['login']
        pr_sender = pr_info['sender']['login']
        pr_repo = pr_info['repository']['full_name']
        pr_org, repo_short_name = pr_repo.split('/')
        try:
            organization = _github_client.get_organization(pr_org)
            repository = organization.get_repo(repo_short_name)
        except UnknownObjectException:
            # If pr_org is not "fetchable" then that means it's a user repository!
            try:
                username = _github_client.get_user(pr_org)
                repository = username.get_repo(repo_short_name)
            except Exception as e:
                raise e

        pull_request = repository.get_pull(pr_number)
        changed_files = pull_request.get_files()
        str_changed_files = ''

        # Get all the protected patterns
        protected_patterns = RepositoryFilePattern.objects.all()

        # We have not yet found a file that violates the protected_patterns list
        found = False
        allowed = False
        # For all the files changed find out if one breaks the rule
        for file in changed_files:
            str_changed_files += file.filename + "\n"
            try:
                for pattern in protected_patterns:
                    if fnmatch.fnmatch(file.filename, pattern.pattern):
                        found = True
                        if pattern.authorized.filter(name=pr_sender).exists():
                            allowed = True
                        else:
                            # If we found out that user hasn't been allowed, the stop immediately
                            allowed = False
                            raise UserNotAllowedException
            except UserNotAllowedException:
                break

        # Publish a comment to the PR stating that the PR Should not be merged
        if found and not allowed:
            pull_request.create_comment(
                "You are not allowed to change a file extension of type '{}'".format(pattern.pattern))

        # Store the transaction result
        result = PullRequestTransactionResult(
            webhook_transaction=transaction,
            action=action,
            number=int(pr_number),
            owner=pr_owner,
            sender=pr_sender,
            repository=repository.full_name,
            changed_files=str_changed_files,
            permission_violation=(found and not allowed)
        )
        result.save()
