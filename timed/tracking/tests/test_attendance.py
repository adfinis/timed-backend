import pytest
from django.urls import reverse
from rest_framework import status

from timed.tracking.factories import AttendanceFactory


def test_attendance_list(auth_client):
    AttendanceFactory.create()
    attendance = AttendanceFactory.create(user=auth_client.user)

    url = reverse("attendance-list")
    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(attendance.id)


def test_attendance_detail(internal_employee_client):
    attendance = AttendanceFactory.create(user=internal_employee_client.user)

    url = reverse("attendance-detail", args=[attendance.id])
    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "is_external, task_assignee__is_resource, expected",
    [
        (False, False, status.HTTP_201_CREATED),
        (True, True, status.HTTP_201_CREATED),
        (True, False, status.HTTP_403_FORBIDDEN),
    ],
)
def test_attendance_create(
    auth_client, employment, is_external, task_assignee, expected
):
    """Should create a new attendance and automatically set the user."""
    user = auth_client.user
    employment.user = user
    task_assignee.user = user
    task_assignee.save()

    if is_external:
        employment.is_external = True
    employment.save()

    data = {
        "data": {
            "type": "attendances",
            "id": None,
            "attributes": {
                "date": "2017-01-01",
                "from-time": "08:00",
                "to-time": "10:00",
            },
        }
    }

    url = reverse("attendance-list")

    response = auth_client.post(url, data)
    assert response.status_code == expected

    if response.status_code == status.HTTP_201_CREATED:
        json = response.json()
        assert json["data"]["relationships"]["user"]["data"]["id"] == str(user.id)


def test_attendance_update(internal_employee_client):
    user = internal_employee_client.user
    attendance = AttendanceFactory.create(user=user)

    data = {
        "data": {
            "type": "attendances",
            "id": attendance.id,
            "attributes": {"to-time": "15:00:00"},
            "relationships": {"user": {"data": {"id": user.id, "type": "users"}}},
        }
    }

    url = reverse("attendance-detail", args=[attendance.id])

    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert (
        json["data"]["attributes"]["to-time"] == data["data"]["attributes"]["to-time"]
    )


def test_attendance_delete(internal_employee_client):
    attendance = AttendanceFactory.create(user=internal_employee_client.user)

    url = reverse("attendance-detail", args=[attendance.id])

    response = internal_employee_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
