from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from rest_framework import status

from timed.employment.factories import (AbsenceTypeFactory, EmploymentFactory,
                                        UserFactory)
from timed.projects.factories import ProjectFactory
from timed.tracking.factories import AbsenceFactory, ReportFactory


def test_user_list_unauthenticated(client):
    url = reverse('user-list')
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_update_unauthenticated(client):
    user = UserFactory.create()
    url = reverse('user-detail', args=[user.id])
    response = client.patch(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_login_ldap(client):
    client.login('ldapuser', 'Test1234!')
    user = get_user_model().objects.get(username='ldapuser')
    assert user.first_name == 'givenName'
    assert user.last_name == 'LdapUser'
    assert user.email == 'ldapuser@example.net'


def test_user_list(auth_client, django_assert_num_queries):
    UserFactory.create_batch(2)

    url = reverse('user-list')

    with django_assert_num_queries(5):
        response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json['data']) == 3


def test_user_detail(auth_client):
    user = auth_client.user

    url = reverse('user-detail', args=[user.id])

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_user_create_authenticated(auth_client):
    url = reverse('user-list')

    response = auth_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_user_create_superuser(superadmin_client):
    url = reverse('user-list')

    data = {
        'data': {
            'type': 'users',
            'id': None,
            'attributes': {
                'is_staff': True,
                'tour_done': True,
                'email': 'test@example.net',
                'first_name': 'First name',
                'last_name': 'Last name',
            },
        }
    }

    response = superadmin_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED


def test_user_update_owner(auth_client):
    user = auth_client.user
    data = {
        'data': {
            'type': 'users',
            'id': user.id,
            'attributes': {
                'is_staff': True,
                'tour_done': True
            },
        }
    }

    url = reverse('user-detail', args=[
        user.id
    ])

    response = auth_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK

    user.refresh_from_db()
    assert user.tour_done
    assert not user.is_staff


def test_user_update_other(auth_client):
    """User may not change other user."""
    user = UserFactory.create()
    url = reverse('user-detail', args=[user.id])
    res = auth_client.patch(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_user_delete_authenticated(auth_client):
    """Should not be able delete a user."""
    user = auth_client.user

    url = reverse('user-detail', args=[user.id])

    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_user_delete_superuser(superadmin_client):
    """Should not be able delete a user."""
    user = UserFactory.create()

    url = reverse('user-detail', args=[user.id])

    response = superadmin_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_user_delete_with_reports_superuser(superadmin_client):
    """Test that user with reports may not be deleted."""
    user = UserFactory.create()
    ReportFactory.create(user=user)

    url = reverse('user-detail', args=[user.id])

    response = superadmin_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_user_supervisor_filter(auth_client):
    """Should filter users by supervisor."""
    supervisees = UserFactory.create_batch(5)

    UserFactory.create_batch(5)

    auth_client.user.supervisees.add(*supervisees)
    auth_client.user.save()

    res = auth_client.get(reverse('user-list'), {
        'supervisor': auth_client.user.id
    })

    assert len(res.json()['data']) == 5


@pytest.mark.freeze_time('2018-01-07')
def test_user_transfer(superadmin_client):
    user = UserFactory.create()
    EmploymentFactory.create(
        user=user, start_date=date(2017, 12, 28), percentage=100
    )
    AbsenceTypeFactory.create(fill_worktime=True)
    AbsenceTypeFactory.create(fill_worktime=False)
    absence_type = AbsenceTypeFactory.create(fill_worktime=False)
    AbsenceFactory.create(
        user=user, type=absence_type, date=date(2017, 12, 29)
    )

    url = reverse('user-transfer', args=[user.id])
    response = superadmin_client.post(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # running transfer twice should lead to same result
    response = superadmin_client.post(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert user.overtime_credits.count() == 1
    overtime_credit = user.overtime_credits.first()
    assert overtime_credit.transfer
    assert overtime_credit.date == date(2018, 1, 1)
    assert overtime_credit.duration == timedelta(hours=-8, minutes=-30)
    assert overtime_credit.comment == 'Transfer 2017'

    assert user.absence_credits.count() == 1
    absence_credit = user.absence_credits.first()
    assert absence_credit.transfer
    assert absence_credit.date == date(2018, 1, 1)
    assert absence_credit.days == -1
    assert absence_credit.comment == 'Transfer 2017'


@pytest.mark.parametrize('value,expected', [(1, 1), (0, 4)])
def test_user_is_reviewer_filter(auth_client, value, expected):
    """Should filter users if they are a reviewer."""
    user = UserFactory.create()
    project = ProjectFactory.create()
    UserFactory.create_batch(3)

    project.reviewers.add(user)

    res = auth_client.get(reverse('user-list'), {'is_reviewer': value})
    assert len(res.json()['data']) == expected
