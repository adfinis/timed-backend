from datetime import timedelta

import redminelib
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.template.loader import get_template
from django.utils.timezone import now

from timed.notifications.models import Notification
from timed.projects.models import Project
from timed.tracking.models import Report

template = get_template("budget_reminder.txt", using="text")


class Command(BaseCommand):
    help = "Check budget of a project and update corresponding Redmine Project."

    def handle(self, *args, **options):
        redmine = redminelib.Redmine(
            settings.REDMINE_URL,
            key=settings.REDMINE_APIKEY,
        )

        projects = (
            Project.objects.filter(
                archived=False,
                cost_center__name__contains=settings.BUILD_PROJECTS,
                redmine_project__isnull=False,
                estimated_time__isnull=False,
                estimated_time__gt=timedelta(hours=0),
            )
            .exclude(notifications__notification_type=Notification.BUDGET_CHECK_70)
            .order_by("name")
        )

        for project in projects.iterator():
            billable_hours = (
                Report.objects.filter(task__project=project, not_billable=False)
                .aggregate(billable_hours=Sum("duration"))
                .get("billable_hours")
            )

            if not billable_hours:
                continue

            billable_hours = billable_hours.total_seconds() / 3600
            estimated_hours = project.estimated_time.total_seconds() / 3600
            budget_percentage = billable_hours / estimated_hours

            if budget_percentage <= 0.3:  # noqa: PLR2004
                continue
            try:
                issue = redmine.issue.get(project.redmine_project.issue_id)
            except redminelib.exceptions.ResourceNotFoundError:
                self.stdout.write(
                    self.style.ERROR(
                        f"Project {project.name} has an invalid Redmine issue {project.redmine_project.issue_id} assigned. Skipping."
                    )
                )
                continue

            notification, _ = Notification.objects.get_or_create(
                notification_type=Notification.BUDGET_CHECK_30
                if budget_percentage <= 0.7  # noqa: PLR2004
                else Notification.BUDGET_CHECK_70,
                project=project,
            )

            if notification.sent_at:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Notification {notification.notification_type} for Project {project.name} already sent. Skipping."
                    )
                )
                continue

            issue.notes = template.render(
                {
                    "estimated_time": estimated_hours,
                    "billable_hours": billable_hours,
                    "budget_percentage": 30
                    if notification.notification_type == Notification.BUDGET_CHECK_30
                    else 70,
                }
            )

            try:
                issue.save()
                notification.sent_at = now()
                notification.save()
            except redminelib.exceptions.BaseRedmineError:  # pragma: no cover
                self.stdout.write(
                    self.style.ERROR(
                        f"Cannot reach Redmine server! Failed to save Redmine issue {issue.id} and notification {notification}"
                    )
                )
