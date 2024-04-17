import pytest
from django.urls import reverse
from rest_framework import status

from timed.conftest import setup_customer_and_employment_status
from timed.employment.factories import EmploymentFactory, LocationFactory


@pytest.mark.django_db()
@pytest.mark.usefixtures("location")
@pytest.mark.parametrize(
    ("is_employed", "is_customer_assignee", "is_customer", "expected"),
    [
        (False, True, True, 0),
        (False, True, False, 0),
        (True, True, True, 2),
        (True, True, False, 2),
        (True, False, False, 2),
    ],
)
def test_location_list(
    auth_client, is_employed, is_customer_assignee, is_customer, expected
):
    setup_customer_and_employment_status(
        user=auth_client.user,
        is_assignee=is_customer_assignee,
        is_customer=is_customer,
        is_employed=is_employed,
        is_external=False,
    )
    url = reverse("location-list")

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()["data"]
    assert len(data) == expected
    if expected:
        assert data[0]["attributes"]["workdays"] == ([str(day) for day in range(1, 6)])


@pytest.mark.parametrize(
    ("is_employed", "expected"),
    [
        (True, status.HTTP_200_OK),
        (False, status.HTTP_404_NOT_FOUND),
    ],
)
def test_location_detail(auth_client, is_employed, expected):
    location = LocationFactory.create()
    if is_employed:
        EmploymentFactory.create(user=auth_client.user)

    url = reverse("location-detail", args=[location.id])

    response = auth_client.get(url)
    assert response.status_code == expected


def test_location_create(auth_client):
    url = reverse("location-list")

    response = auth_client.post(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_location_update(auth_client):
    location = LocationFactory.create()

    url = reverse("location-detail", args=[location.id])

    response = auth_client.patch(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_location_delete(auth_client):
    location = LocationFactory.create()

    url = reverse("location-detail", args=[location.id])

    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
