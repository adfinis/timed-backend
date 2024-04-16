from datetime import date, timedelta

import pytest
from dateutil.rrule import DAILY, FR, MO, rrule
from django.core.management import call_command

from timed.notifications.models import Notification


@pytest.mark.freeze_time("2017-7-27")
def test_notify_supervisors(
    db, mailoutbox, user_factory, employment_factory, task_factory, report_factory
):
    """Test time range 2017-7-17 till 2017-7-23."""
    start = date(2017, 7, 14)
    # supervisee with short time
    supervisee = user_factory.create()
    supervisor = user_factory.create()
    supervisee.supervisors.add(supervisor)

    employment_factory.create(user=supervisee, start_date=start, percentage=100)
    workdays = rrule(
        DAILY,
        dtstart=start,
        until=date.today(),
        # range is excluding last
        byweekday=range(MO.weekday, FR.weekday + 1),
    )
    task = task_factory.create()
    for dt in workdays:
        report_factory.create(
            user=supervisee, date=dt, task=task, duration=timedelta(hours=7)
        )

    call_command("notify_supervisors_shorttime")

    # checks
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [supervisor.email]
    body = mail.body
    assert "Time range: July 17, 2017 - July 23, 2017\nRatio: 0.9" in body
    expected = ("{0} 35.0/42.5 (Ratio 0.82 Delta -7.5 Balance -9.0)").format(
        supervisee.get_full_name()
    )
    assert expected in body
    assert Notification.objects.count() == 1


def test_notify_supervisors_no_employment(db, mailoutbox, user_factory):
    """Check that supervisees without employment do not notify supervisor."""
    supervisee = user_factory.create()
    supervisor = user_factory.create()
    supervisee.supervisors.add(supervisor)

    call_command("notify_supervisors_shorttime")

    assert len(mailoutbox) == 0
    assert Notification.objects.count() == 0
