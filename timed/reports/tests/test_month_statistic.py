from datetime import date, timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from timed.conftest import setup_customer_and_employment_status
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
def test_month_statistic_list(
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

    ReportFactory.create(duration=timedelta(hours=1), date=date(2016, 1, 1))
    ReportFactory.create(duration=timedelta(hours=1), date=date(2015, 12, 4))
    ReportFactory.create(duration=timedelta(hours=2), date=date(2015, 12, 31))

    url = reverse("month-statistic-list")
    result = auth_client.get(url, data={"ordering": "year,month"})
    assert result.status_code == expected
    if expected == status.HTTP_200_OK:
        json = result.json()
        expected_json = [
            {
                "type": "month-statistics",
                "id": "201512",
                "attributes": {"year": 2015, "month": 12, "duration": "03:00:00"},
            },
            {
                "type": "month-statistics",
                "id": "201601",
                "attributes": {"year": 2016, "month": 1, "duration": "01:00:00"},
            },
        ]
        assert json["data"] == expected_json
        assert json["meta"]["total-time"] == "04:00:00"
