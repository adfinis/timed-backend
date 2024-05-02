from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils.duration import duration_string
from rest_framework import status


def test_worktime_balance_create(auth_client):
    url = reverse("worktime-balance-list")

    result = auth_client.post(url)
    assert result.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_worktime_balance_no_employment(auth_client, django_assert_num_queries):
    url = reverse("worktime-balance-list")

    with django_assert_num_queries(3):
        result = auth_client.get(
            url, data={"user": auth_client.user.id, "date": "2017-01-01"}
        )

    assert result.status_code == status.HTTP_200_OK

    json = result.json()
    assert len(json["data"]) == 1
    data = json["data"][0]
    assert data["id"] == f"{auth_client.user.id}_2017-01-01"
    assert data["attributes"]["balance"] == "00:00:00"


def test_worktime_balance_with_employments(
    auth_client,
    django_assert_num_queries,
    employment_factory,
    overtime_credit_factory,
    public_holiday_factory,
    report_factory,
    absence_factory,
):
    # Calculate over one week
    start_date = date(2017, 3, 19)
    end_date = date(2017, 3, 26)

    employment = employment_factory(
        user=auth_client.user,
        start_date=start_date,
        worktime_per_day=timedelta(hours=8, minutes=30),
        end_date=date(2017, 3, 23),
    )
    employment_factory(
        user=auth_client.user,
        start_date=date(2017, 3, 24),
        worktime_per_day=timedelta(hours=8),
        end_date=None,
    )

    # Overtime credit of 10 hours
    overtime_credit_factory.create(
        user=auth_client.user, date=start_date, duration=timedelta(hours=10, minutes=30)
    )

    # One public holiday during workdays
    public_holiday_factory.create(date=start_date, location=employment.location)
    # One public holiday on weekend
    public_holiday_factory.create(
        date=start_date + timedelta(days=1), location=employment.location
    )

    # 2x 10 hour reported worktime
    report_factory.create(
        user=auth_client.user,
        date=start_date + timedelta(days=3),
        duration=timedelta(hours=10),
    )

    report_factory.create(
        user=auth_client.user,
        date=start_date + timedelta(days=4),
        duration=timedelta(hours=10),
    )

    # one absence
    absence_factory.create(user=auth_client.user, date=start_date + timedelta(days=5))

    url = reverse(
        "worktime-balance-detail",
        args=[f"{auth_client.user.id}_{end_date:%Y-%m-%d}"],
    )

    with django_assert_num_queries(11):
        result = auth_client.get(url)
    assert result.status_code == status.HTTP_200_OK

    # 4 workdays 8.5 hours, 1 workday 8 hours, minus one holiday 8.5
    # minutes 10.5 hours overtime credit
    expected_worktime = timedelta(hours=23)

    # 2 x 10 reports hours + 1 absence of 8 hours
    expected_reported = timedelta(hours=28)

    json = result.json()
    assert json["data"]["attributes"]["balance"] == (
        duration_string(expected_reported - expected_worktime)
    )


def test_worktime_balance_invalid_pk(auth_client):
    url = reverse("worktime-balance-detail", args=["invalid"])

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_404_NOT_FOUND


def test_worktime_balance_no_date(auth_client):
    url = reverse("worktime-balance-list")

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_400_BAD_REQUEST


def test_worktime_balance_invalid_date(auth_client):
    url = reverse("worktime-balance-list")

    result = auth_client.get(url, data={"date": "invalid"})
    assert result.status_code == status.HTTP_400_BAD_REQUEST


def test_user_worktime_list_superuser(auth_client, user_factory):
    auth_client.user.is_superuser = True
    auth_client.user.save()
    supervisee = user_factory.create()
    user_factory.create()
    auth_client.user.supervisees.add(supervisee)

    url = reverse("worktime-balance-list")

    result = auth_client.get(url, data={"date": "2017-01-01"})

    assert result.status_code == status.HTTP_200_OK

    json = result.json()
    assert len(json["data"]) == 3


def test_worktime_balance_list_supervisor(auth_client, user_factory):
    supervisee = user_factory.create()
    user_factory.create()
    auth_client.user.supervisees.add(supervisee)

    url = reverse("worktime-balance-list")

    result = auth_client.get(url, data={"date": "2017-01-01"})

    assert result.status_code == status.HTTP_200_OK

    json = result.json()
    assert len(json["data"]) == 2


def test_worktime_balance_list_filter_user(auth_client, user_factory):
    supervisee = user_factory.create()
    user_factory.create()
    auth_client.user.supervisees.add(supervisee)

    url = reverse("worktime-balance-list")

    result = auth_client.get(url, data={"date": "2017-01-01", "user": supervisee.id})

    assert result.status_code == status.HTTP_200_OK

    json = result.json()
    assert len(json["data"]) == 1


def test_worktime_balance_list_last_reported_date_no_reports(
    auth_client, django_assert_num_queries
):
    url = reverse("worktime-balance-list")

    with django_assert_num_queries(1):
        result = auth_client.get(url, data={"last_reported_date": 1})

    assert result.status_code == status.HTTP_200_OK

    json = result.json()
    assert len(json["data"]) == 0


@pytest.mark.freeze_time("2017-02-02")
def test_worktime_balance_list_last_reported_date(
    auth_client, django_assert_num_queries, employment_factory, report_factory
):
    employment_factory(
        user=auth_client.user,
        start_date=date(2017, 2, 1),
        end_date=date(2017, 2, 2),
        worktime_per_day=timedelta(hours=8),
    )

    report_factory(
        user=auth_client.user, date=date(2017, 2, 1), duration=timedelta(hours=10)
    )

    # reports today and in the future should be ignored
    report_factory(
        user=auth_client.user, date=date(2017, 2, 2), duration=timedelta(hours=10)
    )
    report_factory(
        user=auth_client.user, date=date(2017, 2, 3), duration=timedelta(hours=10)
    )

    url = reverse("worktime-balance-list")

    with django_assert_num_queries(9):
        result = auth_client.get(url, data={"last_reported_date": 1})

    assert result.status_code == status.HTTP_200_OK

    json = result.json()
    assert len(json["data"]) == 1
    entry = json["data"][0]
    assert entry["attributes"]["date"] == "2017-02-01"
    assert entry["attributes"]["balance"] == "02:00:00"
