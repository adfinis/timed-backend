from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.template.loader import get_template


def _send_notification_emails(changes, reviewer, rejected=False):
    """Send email for each user."""

    if rejected:
        subject = "[Timed] Your reports have been rejected"
        template = get_template("mail/notify_user_rejected_reports.tmpl", using="text")
    else:
        template = get_template("mail/notify_user_changed_reports.tmpl", using="text")
        subject = "[Timed] Your reports have been changed"
    from_email = settings.DEFAULT_FROM_EMAIL
    connection = get_connection()

    messages = []

    for user_changes in changes:
        user = user_changes["user"]

        body = template.render(
            {
                # we need start and end date in system format
                "reviewer": reviewer,
                "user_changes": user_changes["changes"],
            }
        )

        message = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[user.email],
            connection=connection,
            headers=settings.EMAIL_EXTRA_HEADERS,
        )

        messages.append(message)
    if len(messages) > 0:
        connection.send_messages(messages)


def _get_report_changeset(report, fields):
    changeset = {
        "report": report,
        "changes": {
            key: {"old": getattr(report, key), "new": fields[key]}
            for key in fields.keys()
            # skip if field is not changed or just a reviewer field
            if getattr(report, key) != fields[key]
            and key in settings.TRACKING_REPORT_VERIFIED_CHANGES
        },
    }
    if not changeset["changes"]:
        return False
    return changeset


def notify_user_changed_report(report, fields, reviewer):
    changeset = _get_report_changeset(report, fields)

    if not changeset:
        return

    user_changes = {"user": report.user, "changes": [changeset]}
    _send_notification_emails([user_changes], reviewer)


def notify_user_changed_reports(queryset, fields, reviewer):
    users = [report.user for report in queryset.order_by("user").distinct("user")]
    user_changes = []

    for user in users:
        changes = []
        for report in queryset.filter(user=user).order_by("date"):
            changeset = _get_report_changeset(report, fields)

            # skip edits of own reports and empty changes
            if report.user == reviewer or not changeset:
                continue
            changes.append(changeset)

        # skip user if changes are empty
        if not changes:
            continue

        user_changes.append({"user": user, "changes": changes})

    _send_notification_emails(user_changes, reviewer)


def notify_user_rejected_report(report, reviewer):
    user_changes = {"user": report.user, "changes": [{"report": report}]}
    _send_notification_emails([user_changes], reviewer, True)


def notify_user_rejected_reports(queryset, fields, reviewer):
    users = [report.user for report in queryset.order_by("user").distinct("user")]
    user_changes = []

    for user in users:
        changes = []
        for report in queryset.filter(user=user).order_by("date"):
            changeset = {"report": report}
            changes.append(changeset)
        user_changes.append({"user": user, "changes": changes})

    _send_notification_emails(user_changes, reviewer, True)
