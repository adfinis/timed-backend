import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import get_template, render_to_string
from django.utils.timezone import now

from timed.notifications.models import Notification


def prepare_and_send_email(project, order_duration):
    template_txt = get_template("notify_accountants_order.txt")
    from_email = settings.DEFAULT_FROM_EMAIL
    connection = get_connection()
    messages = []

    customer = project.customer

    duration = order_duration.split(":")
    hours = int(duration[0])
    minutes = int(duration[1])
    hours_added = datetime.timedelta(hours=hours, minutes=minutes)

    hours_total = hours_added
    if project.estimated_time is not None:
        hours_total += project.estimated_time

    subject = f"Customer Center Credits/Reports: {customer.name} has ordered {hours_added} hours."

    body_txt = template_txt.render(
        {
            "customer": customer,
            "project": project,
            "hours_added": hours_added,
            "hours_total": hours_total,
        }
    )
    body_html = render_to_string(
        "notify_accountants_order.html",
        {
            "customer": customer,
            "project": project,
            "hours_added": hours_added,
            "hours_total": hours_total,
        },
    )

    message = EmailMultiAlternatives(
        subject=subject,
        body=body_txt,
        from_email=from_email,
        to=[settings.CUSTOMER_CENTER_EMAIL],
        connection=connection,
        headers=settings.EMAIL_EXTRA_HEADERS,
    )
    message.attach_alternative(body_html, "text/html")

    messages.append(message)
    connection.send_messages(messages)
    Notification.objects.create(
        notification_type=Notification.REVIEWER_UNVERIFIED, sent_at=now()
    )
