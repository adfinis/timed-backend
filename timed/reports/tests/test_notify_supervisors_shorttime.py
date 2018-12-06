from datetime import date, timedelta

import pytest
from dateutil.rrule import DAILY, FR, MO, rrule
from django.core.management import call_command

from timed.employment.factories import EmploymentFactory, UserFactory
from timed.projects.factories import TaskFactory
from timed.tracking.factories import ReportFactory


@pytest.mark.freeze_time('2017-7-27')
def test_notify_supervisors(db, mailoutbox):
    """Test time range 2017-7-17 till 2017-7-23."""
    start = date(2017, 7, 14)
    # supervisee with short time
    supervisee = UserFactory.create()
    supervisor = UserFactory.create()
    supervisee.supervisors.add(supervisor)

    EmploymentFactory.create(user=supervisee,
                             start_date=start,
                             percentage=100)
    workdays = rrule(DAILY, dtstart=start, until=date.today(),
                     # range is excluding last
                     byweekday=range(MO.weekday, FR.weekday + 1))
    task = TaskFactory.create()
    for dt in workdays:
        ReportFactory.create(user=supervisee, date=dt, task=task,
                             duration=timedelta(hours=7))

    call_command('notify_supervisors_shorttime')

    # checks
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [supervisor.email]
    body = mail.body
    assert 'Time range: 17.07.2017 - 23.07.2017\nRatio: 0.9' in body
    expected = (
        '{0} 35.0/42.5 (Ratio 0.82 Delta -7.5 Balance -9.0)'
    ).format(
        supervisee.get_full_name()
    )
    assert expected in body


def test_notify_supervisors_no_employment(db, mailoutbox):
    """Check that supervisees without employment do not notify supervisor."""
    supervisee = UserFactory.create()
    supervisor = UserFactory.create()
    supervisee.supervisors.add(supervisor)

    call_command('notify_supervisors_shorttime')

    assert len(mailoutbox) == 0
