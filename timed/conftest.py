import pytest
from django.contrib.auth import get_user_model

from timed.jsonapi_test_case import JSONAPIClient


@pytest.fixture
def client(db):
    return JSONAPIClient()


@pytest.fixture
def auth_client(db):
    """Return instance of a JSONAPIClient that is logged in as test user."""
    user = get_user_model().objects.create_user(
        username='user',
        password='123qweasd',
        first_name='Test',
        last_name='User',
    )

    client = JSONAPIClient()
    client.user = user
    client.login('user', '123qweasd')
    return client


@pytest.fixture
def admin_client(db):
    """Return json api client logged in as admin user."""
    user = get_user_model().objects.create_user(
        username='admin',
        password='123qweasd',
        first_name='Test',
        last_name='User',
        is_staff=True
    )

    client = JSONAPIClient()
    client.user = user
    client.login('admin', '123qweasd')
    return client
