from django.urls import reverse
from rest_framework import status

from timed.employment.factories import AbsenceTypeFactory


def test_absence_type_list(auth_client):
    AbsenceTypeFactory.create_batch(2)

    url = reverse('absence-type-list')

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json['data']) == 2


def test_absence_type_list_filter_fill_worktime(auth_client):
    absence_type = AbsenceTypeFactory.create(fill_worktime=True)
    AbsenceTypeFactory.create()

    url = reverse('absence-type-list')

    response = auth_client.get(url, data={'fill_worktime': 1})
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json['data']) == 1
    assert json['data'][0]['id'] == str(absence_type.id)


def test_absence_type_detail(auth_client):
    absence_type = AbsenceTypeFactory.create()

    url = reverse('absence-type-detail', args=[
        absence_type.id
    ])

    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK


def test_absence_type_create(auth_client):
    url = reverse('absence-type-list')

    response = auth_client.post(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_absence_type_update(auth_client):
    absence_type = AbsenceTypeFactory.create()

    url = reverse('absence-type-detail', args=[
        absence_type.id
    ])

    response = auth_client.patch(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_absence_type_delete(auth_client):
    absence_type = AbsenceTypeFactory.create()

    url = reverse('absence-type-detail', args=[
        absence_type.id
    ])

    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
