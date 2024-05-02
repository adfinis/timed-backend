import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK


@pytest.mark.usefixtures("package")
def test_subscription_package_list(auth_client):
    url = reverse("subscription-package-list")

    res = auth_client.get(url)
    assert res.status_code == HTTP_200_OK

    json = res.json()
    assert len(json["data"]) == 1


def test_subscription_package_filter_customer(
    auth_client, customer, billing_type, package_factory, project_factory
):
    package = package_factory.create(billing_type=billing_type)
    project_factory.create_batch(2, billing_type=billing_type, customer=customer)

    url = reverse("subscription-package-list")

    res = auth_client.get(url, data={"customer": customer.id})
    assert res.status_code == HTTP_200_OK

    json = res.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(package.id)
