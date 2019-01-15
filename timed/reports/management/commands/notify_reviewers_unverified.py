from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage, get_connection
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.template.loader import render_to_string

from timed.tracking.models import Report


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
        queryset = Report.objects.filter(
            date__range=[start, end], verified_by__isnull=True
        )
        queryset = queryset.annotate(num_reviewers=Count("task__project__reviewers"))
        queryset = queryset.filter(num_reviewers__gt=0)

        return queryset

    def _notify_reviewers(self, start, end, reports, optional_message, cc):
        """Notify reviewers on their unverified reports."""
        User = get_user_model()
        reviewers = User.objects.all_reviewers().filter(email__isnull=False)
        subject = "[Timed] Verification of reports"
        from_email = settings.DEFAULT_FROM_EMAIL
        connection = get_connection()
        messages = []

        for reviewer in reviewers:
            if reports.filter(task__project__reviewers=reviewer).exists():
                body = render_to_string(
                    "mail/notify_reviewers_unverified.txt",
                    {
                        # we need start and end date in system format
                        "start": str(start),
                        "end": str(end),
                        "message": optional_message,
                        "reviewer": reviewer,
                        "protocol": settings.HOST_PROTOCOL,
                        "domain": settings.HOST_DOMAIN,
                    },
                    using="text",
                )

                message = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=from_email,
                    to=[reviewer.email],
                    cc=cc,
                    connection=connection,
                )

                messages.append(message)
        if len(messages) > 0:
            connection.send_messages(messages)
