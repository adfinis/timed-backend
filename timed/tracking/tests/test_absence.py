import datetime

import pytest
from django.urls import reverse
from rest_framework import status

from timed.employment.factories import (
    AbsenceTypeFactory,
    EmploymentFactory,
    PublicHolidayFactory,
    UserFactory,
)
from timed.tracking.factories import AbsenceFactory, ReportFactory


@pytest.mark.parametrize(
    "is_external",
    [True, False],
)
def test_absence_list_authenticated(auth_client, is_external):
    absence = AbsenceFactory.create(user=auth_client.user)

    # overlapping absence with public holidays need to be hidden
    overlap_absence = AbsenceFactory.create(
        user=auth_client.user, date=datetime.date(2018, 1, 1)
    )
    employment = EmploymentFactory.create(
        user=overlap_absence.user, start_date=datetime.date(2017, 12, 31)
    )
    if is_external:
        employment.is_external = True
        employment.save()

    PublicHolidayFactory.create(date=overlap_absence.date, location=employment.location)
    url = reverse("absence-list")

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()

    if not is_external:
        assert len(json["data"]) == 1
        assert json["data"][0]["id"] == str(absence.id)


def test_absence_list_superuser(superadmin_client):
    AbsenceFactory.create_batch(2)

    url = reverse("absence-list")
    response = superadmin_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 2


def test_absence_list_supervisor(internal_employee_client):
    user = UserFactory.create()
    internal_employee_client.user.supervisees.add(user)

    AbsenceFactory.create(user=internal_employee_client.user)
    AbsenceFactory.create(user=user)

    url = reverse("absence-list")
    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 2


def test_absence_list_supervisee(internal_employee_client):
    AbsenceFactory.create(user=internal_employee_client.user)

    supervisors = UserFactory.create_batch(2)

    supervisors[0].supervisees.add(internal_employee_client.user)
    AbsenceFactory.create(user=supervisors[0])

    url = reverse("absence-list")

    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1

    # absences of multiple supervisors shouldn't affect supervisee
    supervisors[1].supervisees.add(internal_employee_client.user)
    AbsenceFactory.create(user=supervisors[1])

    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1


def test_absence_detail(internal_employee_client):
    absence = AbsenceFactory.create(user=internal_employee_client.user)

    url = reverse("absence-detail", args=[absence.id])

    response = internal_employee_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["data"]["id"] == str(absence.id)


@pytest.mark.parametrize(
    "is_external, expected",
    [(False, status.HTTP_201_CREATED), (True, status.HTTP_403_FORBIDDEN)],
)
def test_absence_create(auth_client, is_external, expected):
    user = auth_client.user
    date = datetime.date(2017, 5, 4)
    employment = EmploymentFactory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )
    type = AbsenceTypeFactory.create()

    if is_external:
        employment.is_external = True
        employment.save()

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
            "relationships": {
                "type": {"data": {"type": "absence-types", "id": type.id}}
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


def test_absence_update_owner(auth_client):
    user = auth_client.user
    date = datetime.date(2017, 5, 3)
    absence = AbsenceFactory.create(
        user=auth_client.user, date=datetime.date(2016, 5, 3)
    )
    EmploymentFactory.create(
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


def test_absence_update_superadmin_date(superadmin_client):
    """Test that superadmin may not change date of absence."""
    user = UserFactory.create()
    date = datetime.date(2017, 5, 3)
    absence = AbsenceFactory.create(user=user, date=datetime.date(2016, 5, 3))
    EmploymentFactory.create(
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


def test_absence_update_superadmin_type(superadmin_client):
    """Test that superadmin may not change type of absence."""
    user = UserFactory.create()
    date = datetime.date(2017, 5, 3)
    type = AbsenceTypeFactory.create()
    absence = AbsenceFactory.create(user=user, date=datetime.date(2016, 5, 3))
    EmploymentFactory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )

    data = {
        "data": {
            "type": "absences",
            "id": absence.id,
            "relationships": {
                "type": {"data": {"type": "absence-types", "id": type.id}}
            },
        }
    }

    url = reverse("absence-detail", args=[absence.id])

    response = superadmin_client.patch(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_absence_delete_owner(internal_employee_client):
    absence = AbsenceFactory.create(user=internal_employee_client.user)

    url = reverse("absence-detail", args=[absence.id])

    response = internal_employee_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_absence_delete_superuser(superadmin_client):
    """Test that superuser may not delete absences of other users."""
    user = UserFactory.create()
    absence = AbsenceFactory.create(user=user)

    url = reverse("absence-detail", args=[absence.id])

    response = superadmin_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_absence_fill_worktime(auth_client):
    """Should create an absence which fills the worktime."""
    date = datetime.date(2017, 5, 10)
    user = auth_client.user
    EmploymentFactory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )
    type = AbsenceTypeFactory.create(fill_worktime=True)

    ReportFactory.create(user=user, date=date, duration=datetime.timedelta(hours=5))

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
            "relationships": {
                "type": {"data": {"type": "absence-types", "id": type.id}}
            },
        }
    }

    url = reverse("absence-list")

    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED

    json = response.json()
    assert json["data"]["attributes"]["duration"] == "03:00:00"


def test_absence_fill_worktime_reported_time_to_long(auth_client):
    """
    Verify absence fill worktime is zero when reported time is too long.

    Too long is defined when reported time is longer than worktime per day.
    """
    date = datetime.date(2017, 5, 10)
    user = auth_client.user
    EmploymentFactory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )
    type = AbsenceTypeFactory.create(fill_worktime=True)

    ReportFactory.create(
        user=user, date=date, duration=datetime.timedelta(hours=8, minutes=30)
    )

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
            "relationships": {
                "type": {"data": {"type": "absence-types", "id": type.id}}
            },
        }
    }

    url = reverse("absence-list")

    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED

    json = response.json()
    assert json["data"]["attributes"]["duration"] == "00:00:00"


def test_absence_weekend(auth_client):
    """Should not be able to create an absence on a weekend."""
    date = datetime.date(2017, 5, 14)
    user = auth_client.user
    type = AbsenceTypeFactory.create()
    EmploymentFactory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
            "relationships": {
                "type": {"data": {"type": "absence-types", "id": type.id}}
            },
        }
    }

    url = reverse("absence-list")

    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_absence_public_holiday(auth_client):
    """Should not be able to create an absence on a public holiday."""
    date = datetime.date(2017, 5, 16)
    user = auth_client.user
    type = AbsenceTypeFactory.create()
    employment = EmploymentFactory.create(
        user=user, start_date=date, worktime_per_day=datetime.timedelta(hours=8)
    )
    PublicHolidayFactory.create(location=employment.location, date=date)

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": date.strftime("%Y-%m-%d")},
            "relationships": {
                "type": {"data": {"type": "absence-types", "id": type.id}}
            },
        }
    }

    url = reverse("absence-list")

    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_absence_create_unemployed(auth_client):
    """Test creation of absence fails on unemployed day."""
    type = AbsenceTypeFactory.create()

    data = {
        "data": {
            "type": "absences",
            "id": None,
            "attributes": {"date": "2017-05-16"},
            "relationships": {
                "type": {"data": {"type": "absence-types", "id": type.id}}
            },
        }
    }

    url = reverse("absence-list")

    response = auth_client.post(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_absence_detail_unemployed(internal_employee_client):
    """Test creation of absence fails on unemployed day."""
    absence = AbsenceFactory.create(user=internal_employee_client.user)

    url = reverse("absence-detail", args=[absence.id])

    res = internal_employee_client.get(url)
    assert res.status_code == status.HTTP_200_OK

    json = res.json()
    assert json["data"]["attributes"]["duration"] == "00:00:00"
