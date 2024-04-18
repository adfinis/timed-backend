from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from timed.conftest import setup_customer_and_employment_status


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
def test_customer_statistic_list(
    auth_client,
    is_employed,
    is_customer_assignee,
    is_customer,
    expected,
    status_code,
    django_assert_num_queries,
    report_factory,
):
    user = auth_client.user

    assignee, employment = setup_customer_and_employment_status(
        user=user,
        is_assignee=is_customer_assignee,
        is_customer=is_customer,
        is_employed=is_employed,
        is_external=False,
    )

    # Statistics returns all the customers, not only those
    # with reports. So we must get this one into the expected
    # list as well
    third_customer = assignee.customer if assignee else None

    report = report_factory.create(duration=timedelta(hours=1))
    report_factory.create(duration=timedelta(hours=2), task=report.task)
    report2 = report_factory.create(duration=timedelta(hours=4))

    url = reverse("customer-statistic-list")
    with django_assert_num_queries(expected):
        result = auth_client.get(url, data={"ordering": "duration"})
    assert result.status_code == status_code

    if status_code == status.HTTP_200_OK:
        json = result.json()
        expected_data = [
            {
                "type": "customer-statistics",
                "id": str(report.task.project.customer.id),
                "attributes": {
                    "duration": "03:00:00",
                    "name": report.task.project.customer.name,
                },
            },
            {
                "type": "customer-statistics",
                "id": str(report2.task.project.customer.id),
                "attributes": {
                    "duration": "04:00:00",
                    "name": report2.task.project.customer.name,
                },
            },
        ]
        if third_customer:
            expected_data = [
                {
                    "type": "customer-statistics",
                    "id": str(third_customer.pk),
                    "attributes": {
                        "duration": "00:00:00",
                        "name": third_customer.name,
                    },
                }
            ] + expected_data
        assert json["data"] == expected_data
        assert json["meta"]["total-time"] == "07:00:00"


@pytest.mark.parametrize(
    "filter, expected_result",
    [("from_date", 5), ("customer", 3), ("cost_center", 3), ("reviewer", 3)],
)
def test_customer_statistic_filtered(
    auth_client,
    filter,
    expected_result,
    cost_center,
    report_factory,
    task_factory,
    task_assignee_factory,
    user,
):
    user = auth_client.user
    setup_customer_and_employment_status(
        user=user,
        is_assignee=True,
        is_customer=True,
        is_employed=True,
        is_external=False,
    )

    task_z = task_factory.create(name="Z", cost_center=cost_center)
    task_test = task_factory.create(name="Test")
    reviewer = task_assignee_factory(user=user, task=task_test, is_reviewer=True)

    report_factory.create(
        duration=timedelta(hours=1), date="2022-08-05", task=task_test
    )
    report_factory.create(
        duration=timedelta(hours=2), date="2022-08-30", task=task_test
    )
    report_factory.create(duration=timedelta(hours=3), date="2022-09-01", task=task_z)

    filter_values = {
        "from_date": "2022-08-20",  # last two reports
        "customer": str(task_test.project.customer.pk),  # first two
        "cost_center": str(cost_center.pk),  # first two
        "reviewer": str(reviewer.user.pk),  # first two
    }
    the_filter = {filter: filter_values[filter]}

    url = reverse("customer-statistic-list")
    result = auth_client.get(
        url,
        data={"ordering": "name", **the_filter},
    )
    assert result.status_code == status.HTTP_200_OK

    json = result.json()

    assert json["meta"]["total-time"] == f"{expected_result:02}:00:00"


@pytest.mark.parametrize(
    "is_employed, expected, status_code",
    [
        (True, 5, status.HTTP_200_OK),
        (False, 1, status.HTTP_403_FORBIDDEN),
    ],
)
def test_customer_statistic_detail(
    auth_client,
    is_employed,
    expected,
    status_code,
    django_assert_num_queries,
    employment_factory,
    report_factory,
):
    if is_employed:
        employment_factory.create(user=auth_client.user)
    report = report_factory.create(duration=timedelta(hours=1))

    url = reverse("customer-statistic-detail", args=[report.task.project.customer.id])
    with django_assert_num_queries(expected):
        result = auth_client.get(url, data={"ordering": "duration"})
    assert result.status_code == status_code
    if status_code == status.HTTP_200_OK:
        json = result.json()
        assert json["data"]["attributes"]["duration"] == "01:00:00"
