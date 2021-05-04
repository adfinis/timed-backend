import pytest
from django.core.management import call_command
from redminelib.exceptions import ResourceNotFoundError

from timed.redmine.models import RedmineProject


@pytest.mark.parametrize("not_billable", [False, True])
@pytest.mark.parametrize("review", [False, True])
def test_redmine_report(db, freezer, mocker, report_factory, not_billable, review):
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
    assert "Total hours: {0}".format(report_hours) in issue.notes
    assert "Estimated hours: {0}".format(estimated_hours) in issue.notes
    assert "Hours in last 7 days: {0}\n".format(report_hours) in issue.notes
    assert report.comment in issue.notes
    assert "Not Billable" in issue.notes or not not_billable
    assert "Needs Review" in issue.notes or not review

    assert other.comment not in issue.notes, "Only one new line after report line"
    issue.save.assert_called_once_with()


def test_redmine_report_no_estimated_time(db, freezer, mocker, task, report_factory):
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


def test_redmine_report_invalid_issue(db, freezer, mocker, capsys, report_factory):
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
