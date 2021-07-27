from datetime import timedelta

from django.urls import reverse

from timed.projects.factories import TaskFactory
from timed.tracking.factories import ReportFactory


def test_task_statistic_list(internal_employee_client, django_assert_num_queries):
    task_z = TaskFactory.create(name="Z")
    task_test = TaskFactory.create(name="Test")
    ReportFactory.create(duration=timedelta(hours=1), task=task_test)
    ReportFactory.create(duration=timedelta(hours=2), task=task_test)
    ReportFactory.create(duration=timedelta(hours=2), task=task_z)

    url = reverse("task-statistic-list")
    with django_assert_num_queries(11):
        result = internal_employee_client.get(
            url,
            data={
                "ordering": "task__name",
                "include": "task,task.project,task.project.customer",
            },
        )
    assert result.status_code == 200

    json = result.json()
    expected_json = [
        {
            "type": "task-statistics",
            "id": str(task_test.id),
            "attributes": {"duration": "03:00:00"},
            "relationships": {
                "task": {"data": {"id": str(task_test.id), "type": "tasks"}}
            },
        },
        {
            "type": "task-statistics",
            "id": str(task_z.id),
            "attributes": {"duration": "02:00:00"},
            "relationships": {
                "task": {"data": {"id": str(task_z.id), "type": "tasks"}}
            },
        },
    ]

    assert json["data"] == expected_json
    assert len(json["included"]) == 6
    assert json["meta"]["total-time"] == "05:00:00"
