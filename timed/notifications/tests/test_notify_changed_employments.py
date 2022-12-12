from datetime import date

from django.core.management import call_command

from timed.employment.factories import EmploymentFactory
from timed.notifications.models import Notification


def test_notify_changed_employments(db, mailoutbox, freezer):
    email = "test@example.net"

    # employments changed too far in the past
    freezer.move_to("2017-08-27")
    EmploymentFactory.create_batch(2)

    # employments which should show up in report
    freezer.move_to("2017-09-03")
    finished = EmploymentFactory.create(end_date=date(2017, 10, 10), percentage=80)
    new = EmploymentFactory.create(percentage=100)

    freezer.move_to("2017-09-04")
    call_command("notify_changed_employments", email=email)

    # checks
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [email]
    print(mail.body)
    assert "80% {0}".format(finished.user.get_full_name()) in mail.body
    assert "None       100% {0}".format(new.user.get_full_name()) in mail.body
    assert Notification.objects.all().count() == 1
