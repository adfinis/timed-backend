from datetime import date

import pytest
from django.core.management import call_command

from timed.employment.factories import EmploymentFactory
from timed.notifications.models import Notification


@pytest.mark.django_db()
def test_notify_changed_employments(mailoutbox, freezer):
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
    assert f"80% {finished.user.get_full_name()}" in mail.body
    assert f"None       100% {new.user.get_full_name()}" in mail.body
    assert Notification.objects.all().count() == 1
