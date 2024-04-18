"""Tests for the employments endpoint."""

from datetime import date, timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from timed.employment.admin import EmploymentForm
from timed.employment.models import Employment


def test_employment_create_authenticated(auth_client):
    url = reverse("employment-list")

    result = auth_client.post(url)
    assert result.status_code == status.HTTP_403_FORBIDDEN


def test_employment_create_superuser(superadmin_client, location_factory):
    url = reverse("employment-list")
    location = location_factory.create()

    data = {
        "data": {
            "type": "employments",
            "id": None,
            "attributes": {
                "percentage": "100",
                "worktime_per_day": "08:00:00",
                "start-date": "2017-04-01",
            },
            "relationships": {
                "user": {"data": {"type": "users", "id": superadmin_client.user.id}},
                "location": {"data": {"type": "locations", "id": location.id}},
            },
        }
    }

    result = superadmin_client.post(url, data)
    assert result.status_code == status.HTTP_201_CREATED


def test_employment_update_end_before_start(superadmin_client, employment_factory):
    employment = employment_factory.create(user=superadmin_client.user)

    data = {
        "data": {
            "type": "employments",
            "id": employment.id,
            "attributes": {"start_date": "2017-03-01", "end_date": "2017-01-01"},
        }
    }

    url = reverse("employment-detail", args=[employment.id])
    result = superadmin_client.patch(url, data)
    assert result.status_code == status.HTTP_400_BAD_REQUEST


def test_employment_update_overlapping(superadmin_client, employment_factory):
    user = superadmin_client.user
    employment_factory.create(user=user, end_date=None)
    employment = employment_factory.create(user=user)

    data = {
        "data": {
            "type": "employments",
            "id": employment.id,
            "attributes": {"end_date": None},
        }
    }

    url = reverse("employment-detail", args=[employment.id])
    result = superadmin_client.patch(url, data)
    assert result.status_code == status.HTTP_400_BAD_REQUEST


def test_employment_list_authenticated(auth_client, employment_factory):
    employment_factory.create_batch(2)
    employment = employment_factory.create(user=auth_client.user)

    url = reverse("employment-list")

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_200_OK
    json = result.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(employment.id)


def test_employment_list_superuser(superadmin_client, employment_factory):
    employment_factory.create_batch(2)
    employment_factory.create(user=superadmin_client.user)

    url = reverse("employment-list")

    result = superadmin_client.get(url)
    assert result.status_code == status.HTTP_200_OK
    json = result.json()
    assert len(json["data"]) == 3


def test_employment_list_filter_date(auth_client, employment_factory):
    employment_factory.create(
        user=auth_client.user, start_date=date(2017, 1, 1), end_date=date(2017, 4, 1)
    )
    employment = employment_factory.create(
        user=auth_client.user, start_date=date(2017, 4, 2), end_date=None
    )

    url = reverse("employment-list")

    result = auth_client.get(url, data={"date": "2017-04-05"})
    assert result.status_code == status.HTTP_200_OK
    json = result.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(employment.id)


def test_employment_list_supervisor(auth_client, employment_factory, user_factory):
    user = user_factory.create()
    auth_client.user.supervisees.add(user)

    employment_factory.create_batch(1)
    employment_factory.create(user=auth_client.user)
    employment_factory.create(user=user)

    url = reverse("employment-list")

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_200_OK
    json = result.json()
    assert len(json["data"]) == 2


def test_employment_unique_active(db, employment_factory, user_factory):
    """Should only be able to have one active employment per user."""
    user = user_factory.create()
    employment_factory.create(user=user, end_date=None)
    employment = employment_factory.create(user=user)
    form = EmploymentForm({"end_date": None}, instance=employment)

    with pytest.raises(ValueError):
        form.save()


def test_employment_start_before_end(db, employment_factory):
    employment = employment_factory.create()
    form = EmploymentForm(
        {"start_date": date(2009, 1, 1), "end_date": date(2016, 1, 1)},
        instance=employment,
    )

    with pytest.raises(ValueError):
        form.save()


def test_employment_get_at(db, employment_factory, user_factory):
    """Should return the right employment on a date."""
    user = user_factory.create()
    employment = employment_factory.create(user=user)

    assert Employment.objects.get_at(user, employment.start_date) == employment

    employment.end_date = employment.start_date + timedelta(days=20)

    employment.save()

    with pytest.raises(Employment.DoesNotExist):
        Employment.objects.get_at(user, employment.start_date + timedelta(days=21))


def test_worktime_balance_partial(
    db,
    employment_factory,
    overtime_credit_factory,
    public_holiday_factory,
    report_factory,
):
    """
    Test partial calculation of worktime balance.

    Partial is defined as a worktime balance of a time frame
    which is shorter than employment.
    """
    employment = employment_factory.create(
        start_date=date(2010, 1, 1), end_date=None, worktime_per_day=timedelta(hours=8)
    )
    user = employment.user

    # Calculate over one week
    start = date(2017, 3, 19)
    end = date(2017, 3, 26)

    # Overtime credit of 10.5 hours
    overtime_credit_factory.create(
        user=user, date=start, duration=timedelta(hours=10, minutes=30)
    )

    # One public holiday during workdays
    public_holiday_factory.create(date=start, location=employment.location)
    # One public holiday on weekend
    public_holiday_factory.create(
        date=start + timedelta(days=1), location=employment.location
    )
    # 5 workdays minus one holiday (32 hours)
    expected_expected = timedelta(hours=32)

    # reported 2 days each 10 hours
    for day in range(3, 5):
        report_factory.create(
            user=user, date=start + timedelta(days=day), duration=timedelta(hours=10)
        )
    # 10 hours reported time + 10.5 overtime credit
    expected_reported = timedelta(hours=30, minutes=30)
    expected_balance = expected_reported - expected_expected

    reported, expected, balance = employment.calculate_worktime(start, end)

    assert expected == expected_expected
    assert reported == expected_reported
    assert balance == expected_balance


def test_worktime_balance_longer(
    db,
    employment_factory,
    overtime_credit_factory,
    public_holiday_factory,
    report_factory,
):
    """Test calculation of worktime when frame is longer than employment."""
    employment = employment_factory.create(
        start_date=date(2017, 3, 21),
        end_date=date(2017, 3, 27),
        worktime_per_day=timedelta(hours=8),
    )
    user = employment.user

    # Calculate over one year
    start = date(2017, 1, 1)
    end = date(2017, 12, 31)

    # Overtime credit of 10.5 hours before employment
    overtime_credit_factory.create(
        user=user, date=start, duration=timedelta(hours=10, minutes=30)
    )
    # Overtime credit of during employment
    overtime_credit_factory.create(
        user=user, date=employment.start_date, duration=timedelta(hours=10, minutes=30)
    )

    # One public holiday during employment
    public_holiday_factory.create(
        date=employment.start_date, location=employment.location
    )
    # One public holiday before employment started
    public_holiday_factory.create(date=date(2017, 3, 20), location=employment.location)
    # 5 workdays minus one holiday (32 hours)
    expected_expected = timedelta(hours=32)

    # reported 2 days each 10 hours
    for day in range(3, 5):
        report_factory.create(
            user=user,
            date=employment.start_date + timedelta(days=day),
            duration=timedelta(hours=10),
        )
    # reported time not on current employment
    report_factory.create(
        user=user, date=date(2017, 1, 5), duration=timedelta(hours=10)
    )
    # 10 hours reported time + 10.5 overtime credit
    expected_reported = timedelta(hours=30, minutes=30)
    expected_balance = expected_reported - expected_expected

    reported, expected, balance = employment.calculate_worktime(start, end)

    assert expected == expected_expected
    assert reported == expected_reported
    assert balance == expected_balance


def test_employment_for_user(db, user_factory, employment_factory):
    user = user_factory.create()
    # employment overlapping time frame (early start)
    employment_factory.create(
        start_date=date(2017, 1, 1), end_date=date(2017, 2, 28), user=user
    )
    # employment overlapping time frame (early end)
    employment_factory.create(
        start_date=date(2017, 3, 1), end_date=date(2017, 3, 31), user=user
    )
    # employment within time frame
    employment_factory.create(
        start_date=date(2017, 4, 1), end_date=date(2017, 4, 30), user=user
    )
    # employment without end date
    employment_factory.create(start_date=date(2017, 5, 1), end_date=None, user=user)

    employments = Employment.objects.for_user(user, date(2017, 2, 1), date(2017, 12, 1))

    assert employments.count() == 4
