import sys
from datetime import timedelta

import redminelib
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from django.template.loader import get_template
from django.utils import timezone

from timed.projects.models import Project
from timed.tracking.models import Report

template = get_template("redmine/weekly_report.txt", using="text")


class Command(BaseCommand):
    help = "Update associated Redmine projects and send reports to watchers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--last-days",
            dest="last_days",
            default=7,
            help="Build report of number of last days",
            type=int,
        )

    def handle(self, *args, **options):
        redmine = redminelib.Redmine(
            settings.REDMINE_URL,
            key=settings.REDMINE_APIKEY,
        )

        last_days = options["last_days"]
        # today is excluded
        end = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=last_days)

        # get projects with reports in given last days
        projects = (
            Project.objects.filter(
                archived=False,
                redmine_project__isnull=False,
                tasks__reports__updated__range=[start, end],
            )
            .annotate(count_reports=Count("tasks__reports"))
            .filter(count_reports__gt=0)
            .annotate(total_hours=Sum("tasks__reports__duration"))
            .order_by("name")
        )

        for project in projects:
            estimated_hours = (
                project.estimated_time.total_seconds() / 3600
                if project.estimated_time
                else 0.0
            )
            total_hours = project.total_hours.total_seconds() / 3600
            try:
                issue = redmine.issue.get(project.redmine_project.issue_id)
                reports = Report.objects.filter(
                    task__project=project, updated__range=[start, end]
                ).order_by("date")
                hours = reports.aggregate(hours=Sum("duration"))["hours"]

                issue.notes = template.render(
                    {
                        "project": project,
                        "hours": hours.total_seconds() / 3600,
                        "last_days": last_days,
                        "total_hours": total_hours,
                        "estimated_hours": estimated_hours,
                        "reports": reports,
                    }
                )
                issue.custom_fields = [
                    {"id": settings.REDMINE_SPENTHOURS_FIELD, "value": total_hours}
                ]
                issue.save()
            except redminelib.exceptions.BaseRedmineError:
                sys.stderr.write(
                    "Project {0} has an invalid Redmine "
                    "issue {1} assigned. Skipping".format(
                        project.name, project.redmine_project.issue_id
                    )
                )
