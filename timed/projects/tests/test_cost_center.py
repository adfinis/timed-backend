import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from timed.conftest import setup_customer_and_employment_status
from timed.projects.factories import CostCenterFactory


@pytest.mark.parametrize(
    ("is_employed", "is_customer_assignee", "is_customer", "status_code"),
    [
        (False, True, False, HTTP_403_FORBIDDEN),
        (False, True, True, HTTP_403_FORBIDDEN),
        (True, False, False, HTTP_200_OK),
        (True, True, False, HTTP_200_OK),
        (True, True, True, HTTP_200_OK),
    ],
)
def test_cost_center_list(
    auth_client, is_employed, is_customer_assignee, is_customer, status_code
):
    user = auth_client.user
    cost_center = CostCenterFactory.create()
    setup_customer_and_employment_status(
        user=user,
        is_assignee=is_customer_assignee,
        is_customer=is_customer,
        is_employed=is_employed,
        is_external=False,
    )

    url = reverse("cost-center-list")

    res = auth_client.get(url)
    assert res.status_code == status_code
    if res.status_code == HTTP_200_OK:
        json = res.json()
        assert len(json["data"]) == 1
        assert json["data"][0]["id"] == str(cost_center.id)
