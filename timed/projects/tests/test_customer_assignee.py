import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK


@pytest.mark.parametrize(
    ("is_employed", "is_external", "is_customer_assignee", "is_customer", "expected"),
    [
        (False, False, True, False, 0),
        (False, False, True, True, 0),
        (True, True, False, False, 0),
        (True, False, False, False, 1),
        (True, True, True, False, 0),
        (True, False, True, False, 2),
        (True, True, True, True, 0),
        (True, False, True, True, 2),
    ],
)
def test_customer_assignee_list(
    auth_client,
    is_employed,
    is_external,
    is_customer_assignee,
    is_customer,
    expected,
    setup_customer_and_employment_status,
    customer_assignee,
):
    user = auth_client.user
    setup_customer_and_employment_status(
        user=user,
        is_assignee=is_customer_assignee,
        is_customer=is_customer,
        is_employed=is_employed,
        is_external=is_external,
    )
    url = reverse("customer-assignee-list")

    res = auth_client.get(url)
    assert res.status_code == HTTP_200_OK
    json = res.json()
    assert len(json["data"]) == expected
    if expected:
        assert json["data"][0]["id"] == str(customer_assignee.id)
        assert json["data"][0]["relationships"]["customer"]["data"]["id"] == str(
            customer_assignee.customer.id
        )
