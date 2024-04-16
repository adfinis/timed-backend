from datetime import date, timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from timed.conftest import setup_customer_and_employment_status
from timed.employment.factories import EmploymentFactory
from timed.tracking.factories import ReportFactory


@pytest.mark.parametrize(
    ("is_employed", "is_customer_assignee", "is_customer", "expected"),
    [
        (False, True, False, status.HTTP_403_FORBIDDEN),
        (False, True, True, status.HTTP_403_FORBIDDEN),
        (True, False, False, status.HTTP_200_OK),
        (True, True, False, status.HTTP_200_OK),
        (True, True, True, status.HTTP_200_OK),
    ],
)
def test_year_statistic_list(
    auth_client, is_employed, is_customer_assignee, is_customer, expected
):
    user = auth_client.user
    setup_customer_and_employment_status(
        user=user,
        is_assignee=is_customer_assignee,
        is_customer=is_customer,
        is_employed=is_employed,
        is_external=False,
    )

    ReportFactory.create(duration=timedelta(hours=1), date=date(2017, 1, 1))
    ReportFactory.create(duration=timedelta(hours=1), date=date(2015, 2, 28))
    ReportFactory.create(duration=timedelta(hours=1), date=date(2015, 12, 31))

    url = reverse("year-statistic-list")
    result = auth_client.get(url, data={"ordering": "year"})
    assert result.status_code == expected

    if expected == status.HTTP_200_OK:
        json = result.json()
        expected_json = [
            {
                "type": "year-statistics",
                "id": "2015",
                "attributes": {"year": 2015, "duration": "02:00:00"},
            },
            {
                "type": "year-statistics",
                "id": "2017",
                "attributes": {"year": 2017, "duration": "01:00:00"},
            },
        ]
        assert json["data"] == expected_json
        assert json["meta"]["total-time"] == "03:00:00"


@pytest.mark.parametrize(
    ("is_employed", "expected"),
    [
        (True, status.HTTP_200_OK),
        (False, status.HTTP_403_FORBIDDEN),
    ],
)
def test_year_statistic_detail(auth_client, is_employed, expected):
    if is_employed:
        EmploymentFactory.create(user=auth_client.user)
    ReportFactory.create(duration=timedelta(hours=1), date=date(2015, 2, 28))
    ReportFactory.create(duration=timedelta(hours=1), date=date(2015, 12, 31))

    url = reverse("year-statistic-detail", args=[2015])
    result = auth_client.get(url, data={"ordering": "year"})
    assert result.status_code == expected
    if expected == status.HTTP_200_OK:
        json = result.json()
        assert json["data"]["attributes"]["duration"] == "02:00:00"
