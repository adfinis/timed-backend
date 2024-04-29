from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.parametrize(
    ("is_employed", "is_customer_assignee", "is_customer", "status_code"),
    [
        (False, True, False, status.HTTP_403_FORBIDDEN),
        (False, True, True, status.HTTP_403_FORBIDDEN),
        (True, False, False, status.HTTP_200_OK),
        (True, True, False, status.HTTP_200_OK),
        (True, True, True, status.HTTP_200_OK),
    ],
)
def test_user_statistic_list(
    auth_client,
    is_employed,
    is_customer_assignee,
    is_customer,
    status_code,
    setup_customer_and_employment_status,
    report_factory,
):
    user = auth_client.user
    setup_customer_and_employment_status(
        user=user,
        is_assignee=is_customer_assignee,
        is_customer=is_customer,
        is_employed=is_employed,
        is_external=False,
    )
    report_factory(duration=timedelta(hours=1), user=user)
    report_factory(duration=timedelta(hours=2), user=user)
    report = report_factory(duration=timedelta(hours=2))

    url = reverse("user-statistic-list")
    result = auth_client.get(url, data={"ordering": "duration", "include": "user"})
    assert result.status_code == status_code

    if status_code == status.HTTP_200_OK:
        json = result.json()
        expected_json = [
            {
                "type": "user-statistics",
                "id": str(report.user.id),
                "attributes": {"duration": "02:00:00"},
                "relationships": {
                    "user": {"data": {"id": str(report.user.id), "type": "users"}}
                },
            },
            {
                "type": "user-statistics",
                "id": str(user.id),
                "attributes": {"duration": "03:00:00"},
                "relationships": {
                    "user": {"data": {"id": str(user.id), "type": "users"}}
                },
            },
        ]
        assert json["data"] == expected_json
        assert len(json["included"]) == 2
        assert json["meta"]["total-time"] == "05:00:00"
