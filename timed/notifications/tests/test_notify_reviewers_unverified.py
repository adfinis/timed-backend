from datetime import date

import pytest
from django.core.management import call_command

from timed.notifications.models import Notification


@pytest.mark.freeze_time("2017-8-4")
@pytest.mark.parametrize(
    "cc,message",
    [
        ("", ""),
        ("example@example.com", ""),
        ("example@example.com", "This is a test"),
        ("", "This is a test"),
    ],
)
def test_notify_reviewers_with_cc_and_message(
    db,
    mailoutbox,
    cc,
    message,
    project_factory,
    user_factory,
    task_factory,
    project_assignee_factory,
    report_factory,
):
    """Test time range 2017-7-1 till 2017-7-31."""
    # a reviewer which will be notified
    reviewer_work = user_factory.create()
    project_work = project_factory.create()
    project_assignee_factory.create(
        user=reviewer_work, project=project_work, is_reviewer=True
    )
    task_work = task_factory.create(project=project_work)
    report_factory.create(date=date(2017, 7, 1), task=task_work, verified_by=None)

    # a reviewer which doesn't have any unverfied reports
    reviewer_no_work = user_factory.create()
    project_no_work = project_factory.create()
    project_assignee_factory.create(
        user=reviewer_no_work, project=project_no_work, is_reviewer=True
    )
    task_no_work = task_factory.create(project=project_no_work)
    report_factory.create(
        date=date(2017, 7, 1), task=task_no_work, verified_by=reviewer_no_work
    )

    call_command(
        "notify_reviewers_unverified",
        "--cc={0}".format(cc),
        "--message={0}".format(message),
    )

    # checks
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [reviewer_work.email]
    url = (
        "http://localhost:4200/analysis?fromDate=2017-07-01&"
        "toDate=2017-07-31&reviewer=%d&editable=1"
    ) % reviewer_work.id
    assert url in mail.body
    assert message in mail.body
    assert mail.cc[0] == cc


@pytest.mark.freeze_time("2017-8-4")
def test_notify_reviewers(
    db,
    mailoutbox,
    project_factory,
    project_assignee_factory,
    task_factory,
    report_factory,
    user_factory,
):
    """Test time range 2017-7-1 till 2017-7-31."""
    # a reviewer which will be notified
    reviewer_work = user_factory.create()
    project_work = project_factory.create()
    project_assignee_factory.create(
        user=reviewer_work, project=project_work, is_reviewer=True
    )
    task_work = task_factory.create(project=project_work)
    report_factory.create(date=date(2017, 7, 1), task=task_work, verified_by=None)

    call_command("notify_reviewers_unverified")

    # checks
    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [reviewer_work.email]
    url = (
        "http://localhost:4200/analysis?fromDate=2017-07-01&"
        "toDate=2017-07-31&reviewer=%d&editable=1"
    ) % reviewer_work.id
    assert url in mail.body
    assert Notification.objects.count() == 1


@pytest.mark.freeze_time("2017-8-4")
def test_notify_reviewers_reviewer_hierarchy(
    db,
    mailoutbox,
    project_factory,
    task_factory,
    project_assignee_factory,
    task_assignee_factory,
    report_factory,
    user_factory,
):
    """Test notification with reviewer hierarchy.

    Test if only the lowest in reviewer hierarchy gets notified.
    """
    # user that shouldn't be notified
    project_reviewer = user_factory.create()
    # user that should be notified
    task_reviewer = user_factory.create()
    project = project_factory.create()
    task = task_factory.create(project=project)
    project_assignee_factory.create(
        user=project_reviewer, project=project, is_reviewer=True
    )
    task_assignee_factory.create(user=task_reviewer, task=task, is_reviewer=True)

    report_factory.create(date=date(2017, 7, 1), task=task, verified_by=None)

    call_command("notify_reviewers_unverified")

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [task_reviewer.email]
    url = (
        "http://localhost:4200/analysis?fromDate=2017-07-01&"
        "toDate=2017-07-31&reviewer=%d&editable=1"
    ) % task_reviewer.id
    assert url in mail.body
