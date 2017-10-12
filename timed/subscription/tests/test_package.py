from django.core.urlresolvers import reverse
from rest_framework.status import HTTP_200_OK

from timed.subscription.factories import PackageFactory


def test_subscription_package_list(auth_client):
    PackageFactory.create()

    url = reverse('subscription-package-list')

    res = auth_client.get(url)
    assert res.status_code == HTTP_200_OK

    json = res.json()
    assert len(json['data']) == 1
