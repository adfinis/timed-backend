import pytest
from django.core.management import call_command
from redminelib.exceptions import ResourceNotFoundError

from timed.redmine.models import RedmineProject


@pytest.mark.django_db()
@pytest.mark.parametrize("not_billable", [False, True])
@pytest.mark.parametrize("review", [False, True])
def test_redmine_report(freezer, mocker, report_factory, not_billable, review):
    """
    Test redmine report.

    Simulate reports added on Friday 2017-07-28 and cronjob run on
    Monday 2017-07-31.
    """
    redmine_instance = mocker.MagicMock()
    issue = mocker.MagicMock()
    redmine_instance.issue.get.return_value = issue
    redmine_class = mocker.patch("redminelib.Redmine")
    redmine_class.return_value = redmine_instance

    freezer.move_to("2017-07-28")
    report = report_factory(
        not_billable=not_billable,
        review=review,
    )
    report_hours = report.duration.total_seconds() / 3600
    estimated_hours = report.task.project.estimated_time.total_seconds() / 3600
    RedmineProject.objects.create(project=report.task.project, issue_id=1000)
    # report not attached to redmine
    other = report_factory()

    freezer.move_to("2017-07-31")
    call_command("redmine_report", last_days=7)

    redmine_instance.issue.get.assert_called_once_with(1000)
    assert issue.custom_fields == [{"id": 0, "value": report_hours}]
    assert f"Total hours: {report_hours}" in issue.notes
    assert f"Estimated hours: {estimated_hours}" in issue.notes
    assert f"Hours in last 7 days: {report_hours}\n" in issue.notes
    assert report.comment in issue.notes
    assert "[NB]" in issue.notes or not not_billable
    assert "[Rev]" in issue.notes or not review

    assert other.comment not in issue.notes, "Only one new line after report line"
    issue.save.assert_called_once_with()


@pytest.mark.django_db()
def test_redmine_report_no_estimated_time(freezer, mocker, task, report_factory):
    redmine_instance = mocker.MagicMock()
    issue = mocker.MagicMock()
    redmine_instance.issue.get.return_value = issue
    redmine_class = mocker.patch("redminelib.Redmine")
    redmine_class.return_value = redmine_instance

    freezer.move_to("2017-07-28")
    task.project.estimated_time = None
    task.project.save()
    report = report_factory(task=task)
    RedmineProject.objects.create(project=report.task.project, issue_id=1000)

    freezer.move_to("2017-07-31")
    call_command("redmine_report", last_days=7)

    redmine_instance.issue.get.assert_called_once_with(1000)
    issue.save.assert_called_once_with()


@pytest.mark.django_db()
def test_redmine_report_invalid_issue(freezer, mocker, capsys, report_factory):
    """Test case when issue is not available."""
    redmine_instance = mocker.MagicMock()
    redmine_class = mocker.patch("redminelib.Redmine")
    redmine_class.return_value = redmine_instance
    redmine_instance.issue.get.side_effect = ResourceNotFoundError()

    freezer.move_to("2017-07-28")
    report = report_factory()
    RedmineProject.objects.create(project=report.task.project, issue_id=1000)

    freezer.move_to("2017-07-31")
    call_command("redmine_report", last_days=7)

    _, err = capsys.readouterr()
    assert "issue 1000 assigned" in err


@pytest.mark.django_db()
def test_redmine_report_calculate_total_hours(freezer, mocker, task, report_factory):
    redmine_instance = mocker.MagicMock()
    issue = mocker.MagicMock()
    redmine_instance.issue.get.return_value = issue
    redmine_class = mocker.patch("redminelib.Redmine")
    redmine_class.return_value = redmine_instance

    freezer.move_to("2017-07-15")
    reports = report_factory.create_batch(10, task=task)

    freezer.move_to("2017-07-24")
    reports_last_seven_days = report_factory.create_batch(10, task=task)

    total_hours_last_seven_days = 0
    for report in reports_last_seven_days:
        total_hours_last_seven_days += report.duration.total_seconds() / 3600

    total_hours = 0
    for report in reports + reports_last_seven_days:
        total_hours += report.duration.total_seconds() / 3600

    RedmineProject.objects.create(project=task.project, issue_id=1000)

    freezer.move_to("2017-07-31")
    call_command("redmine_report", last_days=7)

    redmine_instance.issue.get.assert_called_once_with(1000)
    assert f"Total hours: {total_hours}" in issue.notes
    assert f"Hours in last 7 days: {total_hours_last_seven_days}\n" in issue.notes
