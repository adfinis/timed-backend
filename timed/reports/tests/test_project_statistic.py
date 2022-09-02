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
        (True, False, False, 3, status.HTTP_200_OK),
        (True, True, False, 3, status.HTTP_200_OK),
        (True, True, True, 3, status.HTTP_200_OK),
    ],
)
def test_project_statistic_list(
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
    report = ReportFactory.create(duration=timedelta(hours=1))
    ReportFactory.create(duration=timedelta(hours=2), task=report.task)
    report2 = ReportFactory.create(duration=timedelta(hours=4))
    task = TaskFactory(project=report.task.project)
    ReportFactory.create(duration=timedelta(hours=2), task=task)

    url = reverse("project-statistic-list")
    with django_assert_num_queries(expected):
        result = auth_client.get(url, data={"ordering": "duration"})
    assert result.status_code == status_code

    if status_code == status.HTTP_200_OK:
        json = result.json()
        expected_json = [
            {
                "type": "project-statistics",
                "id": str(report2.task.project.id),
                "attributes": {
                    "duration": "04:00:00",
                    "name": report2.task.project.name,
                },
            },
            {
                "type": "project-statistics",
                "id": str(report.task.project.id),
                "attributes": {
                    "duration": "05:00:00",
                    "name": report.task.project.name,
                },
            },
        ]
        assert json["data"] == expected_json
        assert json["meta"]["total-time"] == "09:00:00"
