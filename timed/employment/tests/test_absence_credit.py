from django.urls import reverse
from rest_framework import status

from timed.employment.factories import (AbsenceCreditFactory,
                                        AbsenceTypeFactory, UserFactory)


def test_absence_credit_create_authenticated(auth_client):
    url = reverse('absence-credit-list')

    result = auth_client.post(url)
    assert result.status_code == status.HTTP_403_FORBIDDEN


def test_absence_credit_create_superuser(superadmin_client):
    absence_type = AbsenceTypeFactory.create()

    url = reverse('absence-credit-list')

    data = {
        'data': {
            'type': 'absence-credits',
            'id': None,
            'attributes': {
                'date': '2017-01-01',
                'duration': '01:00:00',
            },
            'relationships': {
                'user': {
                    'data': {
                        'type': 'users',
                        'id': superadmin_client.user.id
                    }
                },
                'absence_type': {
                    'data': {
                        'type': 'absence-types',
                        'id': absence_type.id
                    }
                }
            }
        }
    }

    result = superadmin_client.post(url, data)
    assert result.status_code == status.HTTP_201_CREATED


def test_absence_credit_get_authenticated(auth_client):
    AbsenceCreditFactory.create_batch(2)
    absence_credit = AbsenceCreditFactory.create(user=auth_client.user)
    url = reverse('absence-credit-list')

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_200_OK
    json = result.json()
    assert len(json['data']) == 1
    assert json['data'][0]['id'] == str(absence_credit.id)


def test_absence_credit_get_superuser(superadmin_client):
    AbsenceCreditFactory.create_batch(2)
    AbsenceCreditFactory.create(user=superadmin_client.user)
    url = reverse('absence-credit-list')

    result = superadmin_client.get(url)
    assert result.status_code == status.HTTP_200_OK
    json = result.json()
    assert len(json['data']) == 3


def test_absence_credit_get_supervisor(auth_client):
    user = UserFactory.create()
    auth_client.user.supervisees.add(user)

    AbsenceCreditFactory.create_batch(1)
    AbsenceCreditFactory.create(user=auth_client.user)
    AbsenceCreditFactory.create(user=user)
    url = reverse('absence-credit-list')

    result = auth_client.get(url)
    assert result.status_code == status.HTTP_200_OK
    json = result.json()
    assert len(json['data']) == 2
