"""Tests for the overtime credits endpoint."""

from django.urls import reverse
from rest_framework import status


def test_overtime_credit_create_authenticated(auth_client):
    url = reverse("overtime-credit-list")

    result = auth_client.post(url)
    assert result.status_code == status.HTTP_403_FORBIDDEN


def test_overtime_credit_create_superuser(superadmin_client):
    url = reverse("overtime-credit-list")

    data = {
        "data": {
            "type": "overtime-credits",
            "id": None,
            "attributes": {"date": "2017-01-01", "duration": "01:00:00"},
            "relationships": {
                "user": {"data": {"type": "users", "id": superadmin_client.user.id}}
            },
        }
    }

    result = superadmin_client.post(url, data)
    assert result.status_code == status.HTTP_201_CREATED


def test_overtime_credit_get_authenticated(auth_client, overtime_credit_factory):
    overtime_credit_factory.create_batch(2)
    overtime_credit = overtime_credit_factory.create(user=auth_client.user)
    url = reverse("overtime-credit-list")

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_200_OK
    json = result.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(overtime_credit.id)


def test_overtime_credit_get_superuser(superadmin_client, overtime_credit_factory):
    overtime_credit_factory.create_batch(2)
    overtime_credit_factory.create(user=superadmin_client.user)
    url = reverse("overtime-credit-list")

    result = superadmin_client.get(url)
    assert result.status_code == status.HTTP_200_OK
    json = result.json()
    assert len(json["data"]) == 3


def test_overtime_credit_get_supervisor(
    auth_client, overtime_credit_factory, user_factory
):
    user = user_factory.create()
    auth_client.user.supervisees.add(user)

    overtime_credit_factory.create_batch(1)
    overtime_credit_factory.create(user=auth_client.user)
    overtime_credit_factory.create(user=user)
    url = reverse("overtime-credit-list")

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_200_OK
    json = result.json()
    assert len(json["data"]) == 2
