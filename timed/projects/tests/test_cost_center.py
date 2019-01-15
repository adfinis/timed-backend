from django.urls import reverse
from rest_framework.status import HTTP_200_OK

from timed.projects.factories import CostCenterFactory


def test_cost_center_list(auth_client):
    cost_center = CostCenterFactory.create()
    url = reverse("cost-center-list")

    res = auth_client.get(url)
    assert res.status_code == HTTP_200_OK
    json = res.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(cost_center.id)
