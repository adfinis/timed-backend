from django.urls import reverse
from rest_framework.status import HTTP_200_OK

from timed.projects.factories import BillingTypeFactory


def test_billing_type_list(auth_client):
    billing_type = BillingTypeFactory.create()
    url = reverse("billing-type-list")

    res = auth_client.get(url)
    assert res.status_code == HTTP_200_OK
    json = res.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(billing_type.id)
