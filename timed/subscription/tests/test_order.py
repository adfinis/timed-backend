from django.urls import reverse
from rest_framework import status

from timed.subscription import factories


def test_order_list(auth_client):
    factories.OrderFactory.create()

    url = reverse('subscription-order-list')

    res = auth_client.get(url)
    assert res.status_code == status.HTTP_200_OK

    json = res.json()
    assert len(json['data']) == 1
    assert json['data'][0]['relationships']['project']['data']['type'] == (
        'subscription-projects'
    )


def test_order_delete(auth_client):
    order = factories.OrderFactory.create()

    url = reverse('subscription-order-detail', args=[order.id])

    res = auth_client.delete(url)
    assert res.status_code == status.HTTP_204_NO_CONTENT


def test_order_delete_confirmed(auth_client):
    """Deleting of confirmed order should not be possible."""
    order = factories.OrderFactory(acknowledged=True)

    url = reverse('subscription-order-detail', args=[order.id])

    res = auth_client.delete(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_order_confirm_admin(admin_client):
    """Test that admin use may confirm order."""
    order = factories.OrderFactory.create()

    url = reverse('subscription-order-confirm', args=[order.id])

    res = admin_client.post(url)
    assert res.status_code == status.HTTP_204_NO_CONTENT

    order.refresh_from_db()
    assert order.acknowledged
    assert order.confirmedby == admin_client.user


def test_order_confirm_user(auth_client):
    """Test that default user may not confirm order."""
    order = factories.OrderFactory.create()

    url = reverse('subscription-order-confirm', args=[order.id])

    res = auth_client.post(url)
    assert res.status_code == status.HTTP_403_FORBIDDEN
