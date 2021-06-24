"""Tests for the customers endpoint."""

import pytest
from django.urls import reverse
from rest_framework import status

from timed.projects.factories import CustomerFactory


def test_customer_list_not_archived(internal_employee_client):
    CustomerFactory.create(archived=True)
    customer = CustomerFactory.create(archived=False)

    url = reverse("customer-list")

    response = internal_employee_client.get(url, data={"archived": 0})
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(customer.id)


def test_customer_detail(internal_employee_client):
    customer = CustomerFactory.create()

    url = reverse("customer-detail", args=[customer.id])

    response = internal_employee_client.get(url)
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


@pytest.mark.parametrize("is_assigned, expected", [(True, 1), (False, 0)])
def test_customer_list_external_employee(
    external_employee_client, is_assigned, expected
):
    CustomerFactory.create_batch(4)
    customer = CustomerFactory.create()
    if is_assigned:
        customer.assignees.add(external_employee_client.user)

    url = reverse("customer-list")

    response = external_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == expected
