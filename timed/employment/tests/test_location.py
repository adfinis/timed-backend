from django.urls import reverse
from rest_framework import status

from timed.employment.factories import LocationFactory


def test_location_list(auth_client):
    LocationFactory.create()
    url = reverse("location-list")

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["attributes"]["workdays"] == ([str(day) for day in range(1, 6)])


def test_location_detail(auth_client):
    location = LocationFactory.create()

    url = reverse("location-detail", args=[location.id])

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK


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
