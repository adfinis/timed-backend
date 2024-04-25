import datetime

import pytest
from django.core.management import call_command
from django.utils.timezone import now
from redminelib.exceptions import ResourceNotFoundError

from timed.notifications.factories import NotificationFactory
from timed.notifications.models import Notification
from timed.redmine.models import RedmineProject


@pytest.mark.django_db()
@pytest.mark.parametrize(
    ("duration", "percentage_exceeded", "notification_count"),
    [(1, 0, 0), (3, 0, 0), (4, 30, 1), (8, 70, 2), (0, 0, 0)],
)
def test_budget_check_1(
    mocker, report_factory, duration, percentage_exceeded, notification_count
):
    """Test budget check."""
    redmine_instance = mocker.MagicMock()
    issue = mocker.MagicMock()
    redmine_instance.issue.get.return_value = issue
    redmine_class = mocker.patch("redminelib.Redmine")
    redmine_class.return_value = redmine_instance

    report = report_factory(duration=datetime.timedelta(hours=duration))
    project = report.task.project
    project.estimated_time = datetime.timedelta(hours=10)
    project.save()
    project.cost_center.name = "DEV_BUILD"
    project.cost_center.save()

    if duration == 0:
        report.delete()

    if percentage_exceeded == 70:
        NotificationFactory(
            project=project, notification_type=Notification.BUDGET_CHECK_30
        )

    report_hours = report.duration.total_seconds() / 3600
    estimated_hours = project.estimated_time.total_seconds() / 3600
    RedmineProject.objects.create(project=project, issue_id=1000)

    call_command("budget_check")

    if percentage_exceeded:
        redmine_instance.issue.get.assert_called_once_with(1000)
        assert f"Project exceeded {percentage_exceeded}%" in issue.notes
        assert f"Billable Hours: {report_hours}" in issue.notes
        assert f"Budget: {estimated_hours}\n" in issue.notes

        issue.save.assert_called_once_with()
    assert Notification.objects.all().count() == notification_count


@pytest.mark.django_db()
def test_budget_check_skip_notification(capsys, mocker, report_factory):
    redmine_instance = mocker.MagicMock()
    issue = mocker.MagicMock()
    redmine_instance.issue.get.return_value = issue
    redmine_class = mocker.patch("redminelib.Redmine")
    redmine_class.return_value = redmine_instance

    report = report_factory(duration=datetime.timedelta(hours=5))
    project = report.task.project
    project.estimated_time = datetime.timedelta(hours=10)
    project.save()
    project.cost_center.name = "DEV_BUILD"
    project.cost_center.save()

    notification = NotificationFactory(
        project=project, notification_type=Notification.BUDGET_CHECK_30, sent_at=now()
    )

    RedmineProject.objects.create(project=project, issue_id=1000)

    call_command("budget_check")

    out, _ = capsys.readouterr()
    assert (
        f"Notification {notification.notification_type} for Project {project.name} already sent. Skipping"
        in out
    )


@pytest.mark.django_db()
def test_budget_check_no_estimated_timed(mocker, report_factory):
    redmine_instance = mocker.MagicMock()
    issue = mocker.MagicMock()
    redmine_instance.issue.get.return_value = issue
    redmine_class = mocker.patch("redminelib.Redmine")
    redmine_class.return_value = redmine_instance

    report = report_factory()
    project = report.task.project
    project.estimated_time = datetime.timedelta(hours=0)
    project.save()
    project.cost_center.name = "DEV_BUILD"
    project.cost_center.save()
    RedmineProject.objects.create(project=report.task.project, issue_id=1000)

    call_command("budget_check")

    assert Notification.objects.count() == 0


@pytest.mark.django_db()
def test_budget_check_invalid_issue(mocker, capsys, report_factory):
    redmine_instance = mocker.MagicMock()
    redmine_class = mocker.patch("redminelib.Redmine")
    redmine_class.return_value = redmine_instance
    redmine_instance.issue.get.side_effect = ResourceNotFoundError()

    report = report_factory(duration=datetime.timedelta(hours=4))
    report.task.project.estimated_time = datetime.timedelta(hours=10)
    report.task.project.save()
    report.task.project.cost_center.name = "DEV_BUILD"
    report.task.project.cost_center.save()
    RedmineProject.objects.create(project=report.task.project, issue_id=1000)

    call_command("budget_check")

    out, _ = capsys.readouterr()
    assert "issue 1000 assigned" in out
