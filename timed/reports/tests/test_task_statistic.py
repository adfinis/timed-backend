from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from timed.conftest import setup_customer_and_employment_status
from timed.projects.factories import TaskFactory
from timed.tracking.factories import ReportFactory


@pytest.mark.parametrize(
    "is_employed, is_customer_assignee, is_customer, expected, status_code",
    [
        (False, True, False, 1, status.HTTP_403_FORBIDDEN),
        (False, True, True, 1, status.HTTP_403_FORBIDDEN),
        (True, False, False, 4, status.HTTP_200_OK),
        (True, True, False, 4, status.HTTP_200_OK),
        (True, True, True, 4, status.HTTP_200_OK),
    ],
)
def test_task_statistic_list(
    auth_client,
    is_employed,
    is_customer_assignee,
    is_customer,
    expected,
    status_code,
    django_assert_num_queries,
):
    user = auth_client.user
    setup_customer_and_employment_status(
        user=user,
        is_assignee=is_customer_assignee,
        is_customer=is_customer,
        is_employed=is_employed,
        is_external=False,
    )
    task_z = TaskFactory.create(name="Z")
    task_test = TaskFactory.create(name="Test")
    ReportFactory.create(duration=timedelta(hours=1), task=task_test)
    ReportFactory.create(duration=timedelta(hours=2), task=task_test)
    ReportFactory.create(duration=timedelta(hours=2), task=task_z)

    url = reverse("task-statistic-list")
    with django_assert_num_queries(expected):
        result = auth_client.get(
            url,
            data={
                "ordering": "name",
                "include": "project,project.customer",
            },
        )
    assert result.status_code == status_code

    if status_code == status.HTTP_200_OK:
        json = result.json()
        expected_json = [
            {
                "type": "task-statistics",
                "id": str(task_test.id),
                "attributes": {"duration": "03:00:00"},
                "relationships": {
                    "project": {"data": {"id": str(task_test.project.id), "type": "projects"}}
                },
            },
            {
                "type": "task-statistics",
                "id": str(task_z.id),
                "attributes": {"duration": "02:00:00"},
                "relationships": {
                    "project": {"data": {"id": str(task_z.project.id), "type": "projects"}}
                },
            },
        ]
        assert json["data"] == expected_json
        assert len(json["included"]) == 4
        assert json["meta"]["total-time"] == "05:00:00"
