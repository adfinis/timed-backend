from datetime import date

import pytest
from django.urls import reverse
from rest_framework import status

from timed.conftest import setup_customer_and_employment_status
from timed.employment.factories import EmploymentFactory, PublicHolidayFactory


@pytest.mark.parametrize(
    ("is_employed", "is_customer_assignee", "is_customer", "expected"),
    [
        (False, True, True, 0),
        (False, True, False, 0),
        (True, False, False, 1),
        (True, True, False, 1),
        (True, True, True, 1),
    ],
)
def test_public_holiday_list(
    auth_client, is_employed, is_customer_assignee, is_customer, expected
):
    setup_customer_and_employment_status(
        user=auth_client.user,
        is_assignee=is_customer_assignee,
        is_customer=is_customer,
        is_employed=is_employed,
        is_external=False,
    )
    PublicHolidayFactory.create()
    url = reverse("public-holiday-list")

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == expected


@pytest.mark.parametrize(
    ("is_employed", "expected"),
    [
        (True, status.HTTP_200_OK),
        (False, status.HTTP_404_NOT_FOUND),
    ],
)
def test_public_holiday_detail(auth_client, is_employed, expected):
    public_holiday = PublicHolidayFactory.create()
    if is_employed:
        EmploymentFactory.create(user=auth_client.user)

    url = reverse("public-holiday-detail", args=[public_holiday.id])

    response = auth_client.get(url)
    assert response.status_code == expected


def test_public_holiday_create(auth_client):
    url = reverse("public-holiday-list")

    response = auth_client.post(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_public_holiday_update(auth_client):
    public_holiday = PublicHolidayFactory.create()

    url = reverse("public-holiday-detail", args=[public_holiday.id])

    response = auth_client.patch(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_public_holiday_delete(auth_client):
    public_holiday = PublicHolidayFactory.create()

    url = reverse("public-holiday-detail", args=[public_holiday.id])

    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_public_holiday_year_filter(internal_employee_client):
    PublicHolidayFactory.create(date=date(2017, 1, 1))
    public_holiday = PublicHolidayFactory.create(date=date(2018, 1, 1))

    url = reverse("public-holiday-list")

    response = internal_employee_client.get(url, data={"year": 2018})
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(public_holiday.id)
