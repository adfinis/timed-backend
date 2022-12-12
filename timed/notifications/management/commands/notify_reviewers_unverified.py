from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage, get_connection
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.template.loader import get_template
from django.utils.timezone import now

from timed.notifications.models import Notification
from timed.projects.models import CustomerAssignee, ProjectAssignee, TaskAssignee
from timed.tracking.models import Report

template = get_template("mail/notify_reviewers_unverified.txt", using="text")


class Command(BaseCommand):
    """
    Notify reviewers of projects with unverified reports.

    Notifications will be sent when reviewer has projects with reports
    which are unverified in given time frame.

    Example how it works:

    We have set following options

    Today = Friday 4/8/2017
    Months = 1
    Offset = 5

    with these set reports would be checked between 1/7/2017 and 31/7/2017.
    A notification will be sent to reviewers if there are reports on
    projects where they are added as reviewer.
    """

    help = "Notify reviewers of projects with unverified reports."

    def add_arguments(self, parser):
        parser.add_argument(
            "--months",
            default=1,
            type=int,
            dest="months",
            help="Number of months to check unverified reports in.",
        )
        parser.add_argument(
            "--offset",
            default=5,
            type=int,
            dest="offset",
            help="Period will end today minus given offset.",
        )
        parser.add_argument(
            "--message",
            default="",
            type=str,
            dest="message",
            help="Additional message to send if there are unverified reports",
        )
        parser.add_argument(
            "--cc",
            action="append",
            dest="cc",
            help="List of email addresses where to send a cc",
        )

    def handle(self, *args, **options):
        months = options["months"]
        offset = options["offset"]
        message = options["message"]
        cc = options["cc"]

        today = date.today()
        # -1 as we also skip today
        end = today - timedelta(days=offset - 1)
        # -1 days as first day of month is needed
        start = end - relativedelta(months=months, days=-1)

        reports = self._get_unverified_reports(start, end)
        self._notify_reviewers(start, end, reports, message, cc)

    def _get_unverified_reports(self, start, end):
        """
        Get unverified reports.

        Unverified reports are reports on project which have a reviewer
        assigned but are not verified in given time frame.
        """
        return Report.objects.filter(date__range=[start, end], verified_by__isnull=True)

    def _notify_reviewers(self, start, end, reports, optional_message, cc):
        """Notify reviewers on their unverified reports.

        Only the reviewers lowest in the hierarchy should be notified.
        If a project has a project assignee and a task assignee with reviewer role,
        then only the task assignee should be notified about unverified reports.
        """
        User = get_user_model()
        reviewers = User.objects.all_reviewers().filter(email__isnull=False)
        subject = "[Timed] Verification of reports"
        from_email = settings.DEFAULT_FROM_EMAIL
        connection = get_connection()
        messages = []

        for reviewer in reviewers:
            # unverified reports in which user is customer assignee and responsible reviewer
            reports_customer_assignee_is_reviewer = reports.filter(
                Q(
                    task__project__customer_id__in=CustomerAssignee.objects.filter(
                        is_reviewer=True, user_id=reviewer
                    ).values("customer_id")
                )
            ).exclude(
                Q(
                    task__project_id__in=ProjectAssignee.objects.filter(
                        is_reviewer=True
                    ).values("project_id")
                )
                | Q(
                    task_id__in=TaskAssignee.objects.filter(is_reviewer=True).values(
                        "task_id"
                    )
                )
            )

            # unverified reports in which user is project assignee and responsible reviewer
            reports_project_assignee_is_reviewer = reports.filter(
                Q(
                    task__project_id__in=ProjectAssignee.objects.filter(
                        is_reviewer=True, user_id=reviewer
                    ).values("project_id")
                )
            ).exclude(
                Q(
                    task_id__in=TaskAssignee.objects.filter(is_reviewer=True).values(
                        "task_id"
                    )
                )
            )

            # unverified reports in which user task assignee and responsible reviewer
            reports_task_assignee_is_reviewer = reports.filter(
                Q(
                    task_id__in=TaskAssignee.objects.filter(
                        is_reviewer=True, user_id=reviewer
                    ).values("task_id")
                )
            )
            if (
                reports_customer_assignee_is_reviewer
                | reports_project_assignee_is_reviewer
                | reports_task_assignee_is_reviewer
            ).exists():
                body = template.render(
                    {
                        # we need start and end date in system format
                        "start": str(start),
                        "end": str(end),
                        "message": optional_message,
                        "reviewer": reviewer,
                        "protocol": settings.HOST_PROTOCOL,
                        "domain": settings.HOST_DOMAIN,
                    }
                )

                message = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=from_email,
                    to=[reviewer.email],
                    cc=cc,
                    connection=connection,
                    headers=settings.EMAIL_EXTRA_HEADERS,
                )

                messages.append(message)
        if len(messages) > 0:
            connection.send_messages(messages)
            Notification.objects.create(
                notification_type=Notification.REVIEWER_UNVERIFIED, sent_at=now()
            )
