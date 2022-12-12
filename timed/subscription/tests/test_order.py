from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from timed.notifications.models import Notification
from timed.projects.factories import CustomerAssigneeFactory, ProjectFactory
from timed.subscription import factories


@pytest.mark.parametrize(
    "is_customer, is_accountant, is_superuser",
    [
        (True, False, False),
        (False, True, False),
        (False, False, True),
        (False, False, False),
        (False, False, False),
    ],
)
def test_order_list(auth_client, is_customer, is_accountant, is_superuser):
    """Test which user can see orders."""
    order = factories.OrderFactory.create()
    user = auth_client.user

    if is_customer:
        CustomerAssigneeFactory.create(
            customer=order.project.customer, user=user, is_customer=True
        )
    elif is_accountant:
        user.is_accountant = True
        user.save()
    elif is_superuser:
        user.is_superuser = True
        user.save()

    url = reverse("subscription-order-list")

    res = auth_client.get(url)
    assert res.status_code == status.HTTP_200_OK

    json = res.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["relationships"]["project"]["data"]["type"] == (
        "subscription-projects"
    )


@pytest.mark.parametrize(
    "is_customer, is_accountant, is_superuser, confirmed, expected",
    [
        (True, False, False, True, status.HTTP_403_FORBIDDEN),
        (True, False, False, False, status.HTTP_403_FORBIDDEN),
        (False, True, False, True, status.HTTP_403_FORBIDDEN),
        (False, True, False, False, status.HTTP_204_NO_CONTENT),
        (False, False, True, True, status.HTTP_403_FORBIDDEN),
        (False, False, True, False, status.HTTP_204_NO_CONTENT),
        (False, False, False, True, status.HTTP_403_FORBIDDEN),
        (False, False, False, False, status.HTTP_403_FORBIDDEN),
    ],
)
def test_order_delete(
    auth_client, is_customer, is_accountant, is_superuser, confirmed, expected
):
    """Test which user can delete orders, confirmed or not."""
    order = factories.OrderFactory()
    if confirmed:
        order.acknowledged = True
        order.save()

    user = auth_client.user

    if is_customer:
        CustomerAssigneeFactory.create(
            customer=order.project.customer, user=user, is_customer=True
        )
    elif is_accountant:
        user.is_accountant = True
        user.save()
    elif is_superuser:
        user.is_superuser = True
        user.save()

    url = reverse("subscription-order-detail", args=[order.id])

    res = auth_client.delete(url)
    assert res.status_code == expected


@pytest.mark.parametrize(
    "is_superuser, is_accountant, is_customer, status_code",
    [
        (True, False, False, status.HTTP_204_NO_CONTENT),
        (False, True, False, status.HTTP_204_NO_CONTENT),
        (False, False, True, status.HTTP_403_FORBIDDEN),
        (False, False, False, status.HTTP_403_FORBIDDEN),
    ],
)
def test_order_confirm(
    auth_client, is_superuser, is_accountant, is_customer, status_code
):
    """Test which user may confirm orders."""
    order = factories.OrderFactory.create()
    user = auth_client.user

    if is_superuser:
        user.is_superuser = True
        user.save()
    elif is_accountant:
        user.is_accountant = True
        user.save()
    elif is_customer:
        CustomerAssigneeFactory.create(
            user=user, is_customer=True, customer=order.project.customer
        )

    url = reverse("subscription-order-confirm", args=[order.id])

    res = auth_client.post(url)
    assert res.status_code == status_code

    if status_code == status.HTTP_204_NO_CONTENT:
        order.refresh_from_db()
        assert order.acknowledged
        assert order.confirmedby == auth_client.user


@pytest.mark.parametrize(
    "is_customer, is_accountant, is_superuser, acknowledged, mail_sent, project_estimate, expected",
    [
        (
            True,
            False,
            False,
            True,
            0,
            timedelta(minutes=1),
            status.HTTP_400_BAD_REQUEST,
        ),
        (True, False, False, False, 1, timedelta(hours=1), status.HTTP_201_CREATED),
        (False, True, False, True, 0, timedelta(hours=10), status.HTTP_201_CREATED),
        (False, True, False, False, 0, timedelta(hours=24), status.HTTP_201_CREATED),
        (False, False, True, True, 0, timedelta(hours=50), status.HTTP_201_CREATED),
        (False, False, True, False, 0, timedelta(hours=100), status.HTTP_201_CREATED),
        (False, False, False, True, 0, timedelta(hours=200), status.HTTP_403_FORBIDDEN),
        (False, False, False, False, 0, None, status.HTTP_403_FORBIDDEN),
    ],
)
def test_order_create(
    auth_client,
    mailoutbox,
    is_customer,
    is_accountant,
    is_superuser,
    acknowledged,
    mail_sent,
    project_estimate,
    expected,
):
    """Test which user may create orders.

    Additionally test if for creation of acknowledged/confirmed orders.
    """
    user = auth_client.user
    project = ProjectFactory.create(estimated_time=project_estimate)

    if is_customer:
        CustomerAssigneeFactory.create(
            user=user, is_customer=True, customer=project.customer
        )
    elif is_accountant:
        user.is_accountant = True
        user.save()
    elif is_superuser:
        user.is_superuser = True
        user.save()

    data = {
        "data": {
            "type": "subscription-orders",
            "id": None,
            "attributes": {
                "acknowledged": acknowledged,
                "duration": "00:30:00",
            },
            "relationships": {
                "project": {
                    "data": {"type": "subscription-projects", "id": project.id}
                },
            },
        }
    }

    url = reverse("subscription-order-list")

    response = auth_client.post(url, data)
    assert response.status_code == expected

    assert len(mailoutbox) == mail_sent
    if mail_sent:
        mail = mailoutbox[0]
        url = f"https://my.adfinis-sygroup.ch/timed-admin/{project.id}"
        assert str(project.customer) in mail.body
        assert str(project.name) in mail.body
        assert "0:30:00" in mail.body
        assert url in mail.alternatives[0][0]
        assert Notification.objects.count() == 1


@pytest.mark.parametrize(
    "duration, expected, status_code",
    [
        ("00:30:00", "0:30:00", status.HTTP_201_CREATED),
        ("30:00:00", "1 day, 6:00:00", status.HTTP_201_CREATED),
        ("30:30:00", "1 day, 6:30:00", status.HTTP_201_CREATED),
        ("-00:30:00", "-0:30:00", status.HTTP_400_BAD_REQUEST),
        ("-30:00:00", "-1 day, 6:00:00", status.HTTP_400_BAD_REQUEST),
        ("-30:30:00", "-1 day, 6:30:00", status.HTTP_400_BAD_REQUEST),
    ],
)
def test_order_create_duration(
    auth_client, mailoutbox, duration, expected, status_code
):
    user = auth_client.user
    project = ProjectFactory.create(estimated_time=timedelta(hours=1))
    CustomerAssigneeFactory.create(
        user=user, is_customer=True, customer=project.customer
    )

    data = {
        "data": {
            "type": "subscription-orders",
            "id": None,
            "attributes": {
                "acknowledged": False,
                "duration": duration,
            },
            "relationships": {
                "project": {
                    "data": {"type": "subscription-projects", "id": project.id}
                },
            },
        }
    }

    url = reverse("subscription-order-list")

    response = auth_client.post(url, data)
    assert response.status_code == status_code

    if status_code == status.HTTP_201_CREATED:
        assert len(mailoutbox) == 1

        mail = mailoutbox[0]
        assert expected in mail.body


@pytest.mark.parametrize(
    "is_customer, is_accountant, is_superuser, acknowledged, expected",
    [
        (True, False, False, True, status.HTTP_403_FORBIDDEN),
        (True, False, False, False, status.HTTP_403_FORBIDDEN),
        (False, True, False, True, status.HTTP_200_OK),
        (False, True, False, False, status.HTTP_200_OK),
        (False, False, True, True, status.HTTP_200_OK),
        (False, False, True, False, status.HTTP_200_OK),
        (False, False, False, True, status.HTTP_403_FORBIDDEN),
        (False, False, False, False, status.HTTP_403_FORBIDDEN),
    ],
)
def test_order_update(
    auth_client, is_customer, is_accountant, is_superuser, acknowledged, expected
):
    user = auth_client.user
    order = factories.OrderFactory.create()

    if acknowledged:
        order.acknowledged = True
        order.save()

    if is_customer:
        CustomerAssigneeFactory.create(
            user=user, is_customer=True, customer=order.project.customer
        )
    elif is_accountant:
        user.is_accountant = True
        user.save()
    elif is_superuser:
        user.is_superuser = True
        user.save()

    data = {
        "data": {
            "type": "subscription-orders",
            "id": order.id,
            "attributes": {
                "duration": "50:00:00",
                "acknowledged": True,
            },
        }
    }

    url = reverse("subscription-order-detail", args=[order.id])

    response = auth_client.patch(url, data)
    assert response.status_code == expected
