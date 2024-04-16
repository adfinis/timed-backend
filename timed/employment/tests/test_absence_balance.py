from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status


def test_absence_balance_full_day(
    auth_client,
    django_assert_num_queries,
    absence_credit_factory,
    absence_factory,
    absence_type_factory,
    employment_factory,
):
    day = date(2017, 2, 28)

    user = auth_client.user
    employment_factory.create(user=user, start_date=day)
    absence_type = absence_type_factory.create()

    absence_credit_factory.create(
        date=day, user=user, days=5, absence_type=absence_type
    )

    # credit on different user, may not show up
    absence_credit_factory.create(date=date.today(), absence_type=absence_type)

    absence_factory.create(date=day, user=user, absence_type=absence_type)

    absence_factory.create(
        date=day - timedelta(days=1), user=user, absence_type=absence_type
    )

    url = reverse("absence-balance-list")

    with django_assert_num_queries(6):
        result = auth_client.get(
            url,
            data={
                "date": "2017-03-01",
                "user": user.id,
                "include": "absence_credits,absence_type",
            },
        )

    assert result.status_code == status.HTTP_200_OK
    json = result.json()
    assert len(json["data"]) == 1
    entry = json["data"][0]

    assert entry["id"] == "{0}_{1}_2017-03-01".format(user.id, absence_type.id)
    assert entry["attributes"]["credit"] == 5
    assert entry["attributes"]["used-days"] == 2
    assert entry["attributes"]["used-duration"] is None
    assert entry["attributes"]["balance"] == 3

    assert len(json["included"]) == 2


def test_absence_balance_fill_worktime(
    auth_client,
    django_assert_num_queries,
    absence_factory,
    absence_type_factory,
    employment_factory,
    report_factory,
    user_factory,
):
    day = date(2017, 2, 28)

    user = user_factory.create()
    user.supervisors.add(auth_client.user)
    employment_factory.create(
        user=user, start_date=day, worktime_per_day=timedelta(hours=5)
    )
    absence_type = absence_type_factory.create(fill_worktime=True)

    report_factory.create(
        user=user, date=day + timedelta(days=1), duration=timedelta(hours=4)
    )

    absence_factory.create(
        date=day + timedelta(days=1), user=user, absence_type=absence_type
    )

    absence_factory.create(date=day, user=user, absence_type=absence_type)

    url = reverse("absence-balance-list")
    with django_assert_num_queries(11):
        result = auth_client.get(
            url,
            data={
                "date": "2017-03-01",
                "user": user.id,
                "include": "absence_credits,absence_type",
            },
        )
    assert result.status_code == status.HTTP_200_OK

    json = result.json()
    assert len(json["data"]) == 1
    entry = json["data"][0]

    assert entry["id"] == "{0}_{1}_2017-03-01".format(user.id, absence_type.id)

    assert entry["attributes"]["credit"] is None
    assert entry["attributes"]["balance"] is None
    assert entry["attributes"]["used-days"] is None
    assert entry["attributes"]["used-duration"] == "06:00:00"


def test_absence_balance_detail(auth_client, absence_type_factory):
    user = auth_client.user
    absence_type = absence_type_factory.create()
    url = reverse(
        "absence-balance-detail",
        args=["{0}_{1}_2017-03-01".format(user.id, absence_type.id)],
    )

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_200_OK

    json = result.json()
    entry = json["data"]

    assert entry["attributes"]["credit"] == 0
    assert entry["attributes"]["balance"] == 0
    assert entry["attributes"]["used-days"] == 0
    assert entry["attributes"]["used-duration"] is None


def test_absence_balance_list_none_supervisee(
    auth_client, absence_type_factory, user_factory
):
    url = reverse("absence-balance-list")
    absence_type_factory.create()
    unrelated_user = user_factory.create()

    result = auth_client.get(
        url, data={"user": unrelated_user.id, "date": "2017-01-03"}
    )
    assert result.status_code == status.HTTP_200_OK
    assert len(result.json()["data"]) == 0


def test_absence_balance_detail_none_supervisee(
    auth_client, absence_type_factory, user_factory
):
    url = reverse("absence-balance-list")
    absence_type = absence_type_factory.create()
    unrelated_user = user_factory.create()

    url = reverse(
        "absence-balance-detail",
        args=["{0}_{1}_2017-03-01".format(unrelated_user.id, absence_type.id)],
    )

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_404_NOT_FOUND


def test_absence_balance_invalid_date_in_pk(auth_client):
    url = reverse("absence-balance-detail", args=["1_2_invalid"])

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_404_NOT_FOUND


def test_absence_balance_invalid_user_in_pk(auth_client):
    url = reverse("absence-balance-detail", args=["999999_2_2017-03-01"])

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_404_NOT_FOUND


def test_absence_balance_no_date(auth_client):
    url = reverse("absence-balance-list")

    result = auth_client.get(url, data={"user": auth_client.user.id})
    assert result.status_code == status.HTTP_400_BAD_REQUEST


def test_absence_balance_invalid_date(auth_client):
    url = reverse("absence-balance-list")

    result = auth_client.get(url, data={"user": auth_client.user.id, "date": "invalid"})
    assert result.status_code == status.HTTP_400_BAD_REQUEST


def test_absence_balance_no_user(auth_client):
    url = reverse("absence-balance-list")

    result = auth_client.get(url, data={"date": "2017-03-01"})
    assert result.status_code == status.HTTP_400_BAD_REQUEST


def test_absence_balance_invalid_user(auth_client):
    url = reverse("absence-balance-list")

    result = auth_client.get(url, data={"date": "2017-03-01", "user": "invalid"})
    assert result.status_code == status.HTTP_400_BAD_REQUEST
