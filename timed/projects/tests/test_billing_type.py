import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from timed.conftest import setup_customer_and_employment_status
from timed.projects import factories, models


@pytest.mark.parametrize(
    (
        "is_employed",
        "is_external",
        "is_customer_assignee",
        "is_customer",
        "customer_visible",
        "expected",
        "status_code",
    ),
    [
        (False, False, True, False, False, 0, HTTP_403_FORBIDDEN),
        (False, False, True, True, False, 0, HTTP_200_OK),
        (False, False, True, True, True, 1, HTTP_200_OK),
        (True, False, False, False, False, 1, HTTP_200_OK),
        (True, True, False, False, False, 1, HTTP_403_FORBIDDEN),
        (True, False, True, False, False, 1, HTTP_200_OK),
        (True, True, True, False, False, 1, HTTP_403_FORBIDDEN),
        (True, False, True, True, False, 1, HTTP_200_OK),
        (True, True, True, True, False, 0, HTTP_200_OK),
        (True, False, True, True, True, 1, HTTP_200_OK),
        (True, True, True, True, True, 1, HTTP_200_OK),
    ],
)
def test_billing_type_list(
    auth_client,
    is_employed,
    is_external,
    is_customer_assignee,
    is_customer,
    customer_visible,
    expected,
    status_code,
):
    user = auth_client.user
    setup_customer_and_employment_status(
        user=user,
        is_assignee=is_customer_assignee,
        is_customer=is_customer,
        is_employed=is_employed,
        is_external=is_external,
    )
    if is_customer_assignee:
        customer = models.Customer.objects.get(customer_assignees__user=user)
    else:
        customer = factories.CustomerFactory.create()
    project = factories.ProjectFactory.create(
        customer_visible=customer_visible, customer=customer
    )

    url = reverse("billing-type-list")

    res = auth_client.get(url)
    assert res.status_code == status_code
    if res.status_code == HTTP_200_OK and expected:
        json = res.json()
        assert len(json["data"]) == expected
        assert json["data"][0]["id"] == str(project.billing_type.id)
