from django.urls import reverse
from rest_framework.status import HTTP_200_OK

from timed.projects.factories import BillingTypeFactory, CustomerFactory, ProjectFactory
from timed.subscription.factories import PackageFactory


def test_subscription_package_list(auth_client):
    PackageFactory.create()

    url = reverse("subscription-package-list")

    res = auth_client.get(url)
    assert res.status_code == HTTP_200_OK

    json = res.json()
    assert len(json["data"]) == 1


def test_subscription_package_filter_customer(auth_client):
    customer = CustomerFactory.create()
    billing_type = BillingTypeFactory.create()
    package = PackageFactory.create(billing_type=billing_type)
    ProjectFactory.create_batch(2, billing_type=billing_type, customer=customer)

    url = reverse("subscription-package-list")

    res = auth_client.get(url, data={"customer": customer.id})
    assert res.status_code == HTTP_200_OK

    json = res.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(package.id)
