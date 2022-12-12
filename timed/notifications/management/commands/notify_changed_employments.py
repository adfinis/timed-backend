from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.template.loader import get_template
from django.utils import timezone

from timed.employment.models import Employment
from timed.notifications.models import Notification

template = get_template("mail/notify_changed_employments.txt", using="text")


class Command(BaseCommand):
    """
    Notify given email address on changed employments.

    Notifications will be sent when there are employments
    which changed in given last days.
    """

    help = "Send notification on given email address on changed employments."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            dest="email",
            help="Email address notification is sent to.",
        )
        parser.add_argument(
            "--last-days",
            default=7,
            type=int,
            dest="last_days",
            help="Time frame of last days employment changed.",
        )

    def handle(self, *args, **options):
        email = options["email"]
        last_days = options["last_days"]

        # today is excluded
        end = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=last_days)

        employments = Employment.objects.filter(updated__range=[start, end])
        if employments.exists():
            from_email = settings.DEFAULT_FROM_EMAIL
            subject = "[Timed] Employments changed in last {0} days".format(last_days)
            body = template.render({"employments": employments})
            message = EmailMessage(
                subject=subject,
                body=body,
                from_email=from_email,
                to=[email],
                headers=settings.EMAIL_EXTRA_HEADERS,
            )
            message.send()
            Notification.objects.create(
                notification_type=Notification.CHANGED_EMPLOYMENT,
                sent_at=timezone.now(),
            )
