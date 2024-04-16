import datetime

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.parametrize(
    "is_external",
    [True, False],
)
def test_absence_list_authenticated(
    auth_client,
    is_external,
    absence_factory,
    employment_factory,
    public_holiday_factory,
):
    absence = absence_factory.create(user=auth_client.user)

    # overlapping absence with public holidays need to be hidden
    overlap_absence = absence_factory.create(
        user=auth_client.user, date=datetime.date(2018, 1, 1)
    )
    employment = employment_factory.create(
        user=overlap_absence.user, start_date=datetime.date(2017, 12, 31)
    )
    if is_external:
        employment.is_external = True
        employment.save()

    public_holiday_factory.create(
        date=overlap_absence.date, location=employment.location
    )
    url = reverse("absence-list")

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()

    if not is_external:
        assert len(json["data"]) == 1
        assert json["data"][0]["id"] == str(absence.id)


def test_absence_list_superuser(superadmin_client, absence_factory):
    absence_factory.create_batch(2)

    url = reverse("absence-list")
    response = superadmin_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 2


def test_absence_list_supervisor(internal_employee_client, user, absence_factory):
    internal_employee_client.user.supervisees.add(user)

    absence_factory.create(user=internal_employee_client.user)
    absence_factory.create(user=user)

    url = reverse("absence-list")
    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 2


def test_absence_list_supervisee(
    internal_employee_client, absence_factory, user_factory
):
    absence_factory.create(user=internal_employee_client.user)

    supervisors = user_factory.create_batch(2)

    supervisors[0].supervisees.add(internal_employee_client.user)
    absence_factory.create(user=supervisors[0])

    url = reverse("absence-list")

    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1

    # absences of multiple supervisors shouldn't affect supervisee
    supervisors[1].supervisees.add(internal_employee_client.user)
    absence_factory.create(user=supervisors[1])

    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1


def test_absence_detail(internal_employee_client, absence_factory):
    absence = absence_factory.create(user=internal_employee_client.user)

    url = reverse("absence-detail", args=[absence.id])

    response = internal_employee_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["data"]["id"] == str(absence.id)


@pytest.mark.parametrize(
    "is_external, expected",
    [(False, status.HTTP_201_CREATED), (True, status.HTTP_403_FORBIDDEN)],
)
def test_absence_create(
    auth_client, is_external, expected, employment_factory, absence_type_factory
):
    user = auth_client.user
    date = datetime.date(2017, 5, 4)
    employment = employment_factory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )
    absence_type = absence_type_factory.create()

    if is_external:
        employment.is_external = True
        employment.save()

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
            "relationships": {
                "absence_type": {
                    "data": {"type": "absence-types", "id": absence_type.id}
                }
            },
        }
    }

    url = reverse("absence-list")

    response = auth_client.post(url, data)

    assert response.status_code == expected

    if response.status_code == status.HTTP_201_CREATED:
        json = response.json()
        assert json["data"]["relationships"]["user"]["data"]["id"] == (
            str(auth_client.user.id)
        )


def test_absence_update_owner(auth_client, absence_factory, employment_factory):
    user = auth_client.user
    date = datetime.date(2017, 5, 3)
    absence = absence_factory.create(
        user=auth_client.user, date=datetime.date(2016, 5, 3)
    )
    employment_factory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )

    data = {
        "data": {
            "type": "absences",
            "id": absence.id,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
        }
    }

    url = reverse("absence-detail", args=[absence.id])

    response = auth_client.patch(url, data)

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["data"]["attributes"]["date"] == "2017-05-03"


def test_absence_update_superadmin_date(
    superadmin_client, user, absence_factory, employment_factory
):
    """Test that superadmin may not change date of absence."""
    date = datetime.date(2017, 5, 3)
    absence = absence_factory.create(user=user, date=datetime.date(2016, 5, 3))
    employment_factory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )

    data = {
        "data": {
            "type": "absences",
            "id": absence.id,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
        }
    }

    url = reverse("absence-detail", args=[absence.id])

    response = superadmin_client.patch(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_absence_update_superadmin_type(
    superadmin_client, user, absence_type, absence_factory, employment_factory
):
    """Test that superadmin may not change type of absence."""
    date = datetime.date(2017, 5, 3)

    absence = absence_factory.create(user=user, date=datetime.date(2016, 5, 3))
    employment_factory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )

    data = {
        "data": {
            "type": "absences",
            "id": absence.id,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
            "relationships": {
                "absence_type": {
                    "data": {"type": "absence-types", "id": absence_type.id}
                }
            },
        }
    }

    url = reverse("absence-detail", args=[absence.id])

    response = superadmin_client.patch(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_absence_delete_owner(internal_employee_client, absence_factory):
    absence = absence_factory.create(user=internal_employee_client.user)

    url = reverse("absence-detail", args=[absence.id])

    response = internal_employee_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_absence_delete_superuser(superadmin_client, user, absence_factory):
    """Test that superuser may not delete absences of other users."""
    absence = absence_factory.create(user=user)

    url = reverse("absence-detail", args=[absence.id])

    response = superadmin_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_absence_fill_worktime(
    auth_client, employment_factory, absence_type_factory, report_factory
):
    """Should create an absence which fills the worktime."""
    date = datetime.date(2017, 5, 10)
    user = auth_client.user
    employment_factory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )
    absence_type = absence_type_factory.create(fill_worktime=True)

    report_factory.create(user=user, date=date, duration=datetime.timedelta(hours=5))

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
            "relationships": {
                "absence_type": {
                    "data": {"type": "absence-types", "id": absence_type.id}
                }
            },
        }
    }

    url = reverse("absence-list")

    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED

    json = response.json()
    assert json["data"]["attributes"]["duration"] == "03:00:00"


def test_absence_fill_worktime_reported_time_to_long(
    auth_client, employment_factory, absence_type_factory, report_factory
):
    """
    Verify absence fill worktime is zero when reported time is too long.

    Too long is defined when reported time is longer than worktime per day.
    """
    date = datetime.date(2017, 5, 10)
    user = auth_client.user
    employment_factory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )
    absence_type = absence_type_factory.create(fill_worktime=True)

    report_factory.create(
        user=user, date=date, duration=datetime.timedelta(hours=8, minutes=30)
    )

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
            "relationships": {
                "absence_type": {
                    "data": {"type": "absence-types", "id": absence_type.id}
                }
            },
        }
    }

    url = reverse("absence-list")

    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED

    json = response.json()
    assert json["data"]["attributes"]["duration"] == "00:00:00"


def test_absence_weekend(auth_client, absence_type, employment_factory):
    """Should not be able to create an absence on a weekend."""
    date = datetime.date(2017, 5, 14)
    user = auth_client.user
    employment_factory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
            "relationships": {
                "absence_type": {
                    "data": {"type": "absence-types", "id": absence_type.id}
                }
            },
        }
    }

    url = reverse("absence-list")

    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_absence_public_holiday(
    auth_client, absence_type, employment_factory, public_holiday_factory
):
    """Should not be able to create an absence on a public holiday."""
    date = datetime.date(2017, 5, 16)
    user = auth_client.user
    employment = employment_factory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )
    public_holiday_factory.create(location=employment.location, date=date)

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
            "relationships": {
                "absence_type": {
                    "data": {"type": "absence-types", "id": absence_type.id}
                }
            },
        }
    }

    url = reverse("absence-list")

    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_absence_create_unemployed(auth_client, absence_type):
    """Test creation of absence fails on unemployed day."""

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": "2017-05-16"},
            "relationships": {
                "absence_type": {
                    "data": {"type": "absence-types", "id": absence_type.id}
                }
            },
        }
    }

    url = reverse("absence-list")

    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_absence_detail_unemployed(internal_employee_client, absence_factory):
    """Test creation of absence fails on unemployed day."""
    absence = absence_factory.create(user=internal_employee_client.user)

    url = reverse("absence-detail", args=[absence.id])

    res = internal_employee_client.get(url)
    assert res.status_code == status.HTTP_200_OK

    json = res.json()
    assert json["data"]["attributes"]["duration"] == "00:00:00"
