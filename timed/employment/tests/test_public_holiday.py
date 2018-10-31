from datetime import date

from django.urls import reverse
from rest_framework import status

from timed.employment.factories import PublicHolidayFactory


def test_public_holiday_list(auth_client):
    PublicHolidayFactory.create()
    url = reverse('public-holiday-list')

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json['data']) == 1


def test_public_holiday_detail(auth_client):
    public_holiday = PublicHolidayFactory.create()

    url = reverse('public-holiday-detail', args=[
        public_holiday.id
    ])

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_public_holiday_create(auth_client):
    url = reverse('public-holiday-list')

    response = auth_client.post(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_public_holiday_update(auth_client):
    public_holiday = PublicHolidayFactory.create()

    url = reverse('public-holiday-detail', args=[
        public_holiday.id
    ])

    response = auth_client.patch(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_public_holiday_delete(auth_client):
    public_holiday = PublicHolidayFactory.create()

    url = reverse('public-holiday-detail', args=[
        public_holiday.id
    ])

    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_public_holiday_year_filter(auth_client):
    PublicHolidayFactory.create(date=date(2017, 1, 1))
    public_holiday = PublicHolidayFactory.create(date=date(2018, 1, 1))

    url = reverse('public-holiday-list')

    response = auth_client.get(url, data={'year': 2018})
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json['data']) == 1
    assert json['data'][0]['id'] == str(public_holiday.id)
