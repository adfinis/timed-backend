"""Tests for the customers endpoint."""
from datetime import date

from django.urls import reverse
from rest_framework import status

from timed.employment.factories import EmploymentFactory
from timed.projects.factories import CustomerFactory


def test_customer_list_not_archived(auth_client):
    CustomerFactory.create(archived=True)
    customer = CustomerFactory.create(archived=False)

    url = reverse("customer-list")

    response = auth_client.get(url, data={"archived": 0})
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(customer.id)


def test_customer_detail(auth_client):
    customer = CustomerFactory.create()

    url = reverse("customer-detail", args=[customer.id])

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_customer_create(auth_client):
    url = reverse("customer-list")

    response = auth_client.post(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_customer_update(auth_client):
    customer = CustomerFactory.create()

    url = reverse("customer-detail", args=[customer.id])

    response = auth_client.patch(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_customer_delete(auth_client):
    customer = CustomerFactory.create()

    url = reverse("customer-detail", args=[customer.id])

    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_customer_list_external_user(auth_client):
    EmploymentFactory.create(user=auth_client.user, is_external=True)
    CustomerFactory.create_batch(4)
    customer = CustomerFactory.create()
    customer.assignees.add(auth_client.user)

    url = reverse("customer-list")

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1


def test_customer_list_temporary_external_user(auth_client):
    EmploymentFactory.create(
        user=auth_client.user, is_external=True, end_date=date.today()
    )
    CustomerFactory.create_batch(4)
    customer = CustomerFactory.create()
    customer.assignees.add(auth_client.user)

    url = reverse("customer-list")

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
