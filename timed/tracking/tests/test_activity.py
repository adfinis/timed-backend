from datetime import date, time, timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from timed.employment.factories import EmploymentFactory
from timed.tracking.factories import ActivityFactory


def test_activity_list(internal_employee_client):
    activity = ActivityFactory.create(user=internal_employee_client.user)
    url = reverse("activity-list")

    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(activity.id)


def test_activity_detail(internal_employee_client):
    activity = ActivityFactory.create(user=internal_employee_client.user)

    url = reverse("activity-detail", args=[activity.id])

    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "task_assignee__is_resource, task_assignee__is_reviewer, is_external, expected",
    [
        (True, False, True, status.HTTP_201_CREATED),
        (False, True, True, status.HTTP_403_FORBIDDEN),
        (True, False, False, status.HTTP_201_CREATED),
        (False, True, False, status.HTTP_201_CREATED),
    ],
)
def test_activity_create(auth_client, is_external, task_assignee, expected):
    """Should create a new activity and automatically set the user."""
    user = auth_client.user
    employment = EmploymentFactory(user=user)

    if is_external:
        employment.is_external = True
        employment.save()

    task_assignee.user = user
    task_assignee.save()
    task = task_assignee.task

    data = {
        "data": {
            "type": "activities",
            "id": None,
            "attributes": {
                "from-time": "08:00",
                "date": "2017-01-01",
                "comment": "Test activity",
            },
            "relationships": {"task": {"data": {"type": "tasks", "id": task.id}}},
        }
    }

    url = reverse("activity-list")

    response = auth_client.post(url, data)
    assert response.status_code == expected

    if response.status_code == status.HTTP_201_CREATED:
        json = response.json()
        assert int(json["data"]["relationships"]["user"]["data"]["id"]) == int(user.id)


@pytest.mark.parametrize(
    "task_assignee__is_resource, task_assignee__is_reviewer, is_external, expected",
    [
        (True, False, True, status.HTTP_200_OK),
        (False, True, True, status.HTTP_403_FORBIDDEN),
        (True, False, False, status.HTTP_200_OK),
        (False, True, False, status.HTTP_200_OK),
    ],
)
def test_activity_update(auth_client, is_external, task_assignee, expected):
    user = auth_client.user
    activity = ActivityFactory.create(user=user, task=task_assignee.task)
    task_assignee.user = user
    task_assignee.save()
    employment = EmploymentFactory(user=user)

    if is_external:
        employment.is_external = True
        employment.save()

    data = {
        "data": {
            "type": "activities",
            "id": activity.id,
            "attributes": {"comment": "Test activity 2"},
        }
    }

    url = reverse("activity-detail", args=[activity.id])

    response = auth_client.patch(url, data)
    assert response.status_code == expected

    if response.status_code == status.HTTP_200_OK:
        json = response.json()
        assert (
            json["data"]["attributes"]["comment"]
            == data["data"]["attributes"]["comment"]
        )


@pytest.mark.parametrize(
    "task_assignee__is_resource, task_assignee__is_reviewer, is_external, expected",
    [
        (True, False, True, status.HTTP_204_NO_CONTENT),
        (False, True, True, status.HTTP_403_FORBIDDEN),
        (True, False, False, status.HTTP_204_NO_CONTENT),
        (False, True, False, status.HTTP_204_NO_CONTENT),
    ],
)
def test_activity_delete(auth_client, is_external, task_assignee, expected):
    user = auth_client.user
    task_assignee.user = user
    task_assignee.save()
    activity = ActivityFactory.create(user=user, task=task_assignee.task)

    employment = EmploymentFactory(user=user)

    if is_external:
        employment.is_external = True
        employment.save()

    url = reverse("activity-detail", args=[activity.id])

    response = auth_client.delete(url)
    assert response.status_code == expected


def test_activity_list_filter_active(internal_employee_client):
    user = internal_employee_client.user
    activity1 = ActivityFactory.create(user=user)
    activity2 = ActivityFactory.create(user=user, to_time=None, task=activity1.task)

    url = reverse("activity-list")

    response = internal_employee_client.get(url, data={"active": "true"})
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(activity2.id)


def test_activity_list_filter_day(internal_employee_client):
    user = internal_employee_client.user
    day = date(2016, 2, 2)
    ActivityFactory.create(date=day - timedelta(days=1), user=user)
    activity = ActivityFactory.create(date=day, user=user)

    url = reverse("activity-list")
    response = internal_employee_client.get(url, data={"day": day.strftime("%Y-%m-%d")})
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(activity.id)


def test_activity_create_no_task(internal_employee_client):
    """Should create a new activity without a task."""
    data = {
        "data": {
            "type": "activities",
            "id": None,
            "attributes": {
                "from-time": "08:00",
                "date": "2017-01-01",
                "comment": "Test activity",
            },
            "relationships": {"task": {"data": None}},
        }
    }

    url = reverse("activity-list")
    response = internal_employee_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED

    json = response.json()
    assert json["data"]["relationships"]["task"]["data"] is None


def test_activity_active_unique(internal_employee_client):
    """Should not be able to have two active blocks."""
    ActivityFactory.create(user=internal_employee_client.user, to_time=None)

    data = {
        "data": {
            "type": "activities",
            "id": None,
            "attributes": {
                "from-time": "08:00",
                "date": "2017-01-01",
                "comment": "Test activity",
            },
        }
    }

    url = reverse("activity-list")

    res = internal_employee_client.post(url, data)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    json = res.json()
    assert json["errors"][0]["detail"] == ("A user can only have one active activity")


def test_activity_to_before_from(internal_employee_client):
    """Test that to is not before from."""
    activity = ActivityFactory.create(
        user=internal_employee_client.user, from_time=time(7, 30), to_time=None
    )

    data = {
        "data": {
            "type": "activities",
            "id": activity.id,
            "attributes": {"to-time": "07:00"},
        }
    }

    url = reverse("activity-detail", args=[activity.id])

    res = internal_employee_client.patch(url, data)

    assert res.status_code == status.HTTP_400_BAD_REQUEST
    json = res.json()
    assert json["errors"][0]["detail"] == (
        "An activity block may not end before it starts."
    )


def test_activity_not_editable(internal_employee_client):
    """Test that transferred activities are read only."""
    activity = ActivityFactory.create(
        user=internal_employee_client.user, transferred=True
    )

    data = {
        "data": {
            "type": "activities",
            "id": activity.id,
            "attributes": {"comment": "Changed Comment"},
        }
    }

    url = reverse("activity-detail", args=[activity.id])
    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_activity_retrievable_not_editable(internal_employee_client):
    """Test that transferred activities are still retrievable."""
    activity = ActivityFactory.create(
        user=internal_employee_client.user, transferred=True
    )

    url = reverse("activity-detail", args=[activity.id])

    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_activity_active_update(internal_employee_client):
    activity = ActivityFactory.create(user=internal_employee_client.user, to_time=None)

    data = {
        "data": {
            "type": "activities",
            "id": activity.id,
            "attributes": {"from-time": "08:00", "comment": "Changed Comment"},
        }
    }

    url = reverse("activity-detail", args=[activity.id])
    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert (
        json["data"]["attributes"]["comment"] == data["data"]["attributes"]["comment"]
    )


def test_activity_set_to_time_none(internal_employee_client, activity_factory):
    activity1 = activity_factory(user=internal_employee_client.user, to_time=None)
    activity2 = activity_factory(
        user=internal_employee_client.user, task=activity1.task
    )

    data = {
        "data": {
            "type": "activities",
            "id": activity2.id,
            "attributes": {"to-time": None},
        }
    }

    url = reverse("activity-detail", args=[activity2.id])

    res = internal_employee_client.patch(url, data)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
