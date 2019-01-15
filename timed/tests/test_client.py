import pytest
from django.contrib.auth import get_user_model
from rest_framework import exceptions

from timed.tests.client import JSONAPIClient


def test_client_login(db):
    get_user_model().objects.create_user(
        username="user", password="123qweasd", first_name="Test", last_name="User"
    )

    client = JSONAPIClient()
    client.login("user", "123qweasd")


def test_client_login_fails(db):
    client = JSONAPIClient()
    with pytest.raises(exceptions.AuthenticationFailed):
        client.login("someuser", "invalidpw")
