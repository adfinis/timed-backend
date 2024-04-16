import hashlib
import json

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from mozilla_django_oidc.contrib.drf import OIDCAuthentication
from requests.exceptions import HTTPError
from rest_framework import exceptions, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.reverse import reverse

from timed.employment.factories import UserFactory


@pytest.mark.django_db()
@pytest.mark.parametrize("is_id_token", [True, False])
@pytest.mark.parametrize(
    ("authentication_header", "error"),
    [
        ("", False),
        ("Bearer", True),
        ("Bearer Too many params", True),
        ("Basic Auth", True),
        ("Bearer Token", False),
    ],
)
@pytest.mark.parametrize("user__username", ["1"])
def test_authentication(
    user,
    rf,
    authentication_header,
    error,
    is_id_token,
    requests_mock,
    settings,
):
    userinfo = {"sub": "1"}
    requests_mock.get(settings.OIDC_OP_USER_ENDPOINT, text=json.dumps(userinfo))

    if not is_id_token:
        userinfo = {"client_id": "test_client", "sub": "1"}
        requests_mock.get(
            settings.OIDC_OP_USER_ENDPOINT, status_code=status.HTTP_401_UNAUTHORIZED
        )
        requests_mock.post(
            settings.OIDC_OP_INTROSPECT_ENDPOINT, text=json.dumps(userinfo)
        )

    request = rf.get("/openid", HTTP_AUTHORIZATION=authentication_header)
    try:
        result = OIDCAuthentication().authenticate(request)
    except exceptions.AuthenticationFailed:
        assert error
    else:
        if result:
            key = "userinfo" if is_id_token else "introspection"
            user, auth = result
            assert user.is_authenticated
            assert (
                cache.get(f"auth.{key}.{hashlib.sha256(b'Token').hexdigest()}")
                == userinfo
            )


@pytest.mark.django_db()
@pytest.mark.parametrize(
    ("create_user", "username", "expected_count"),
    [(False, "", 0), (True, "", 1), (True, "foo@example.com", 1)],
)
def test_authentication_new_user(
    rf, requests_mock, settings, create_user, username, expected_count
):
    settings.OIDC_CREATE_USER = create_user
    user_model = get_user_model()
    assert user_model.objects.filter(username=username).count() == 0

    userinfo = {"sub": username}
    requests_mock.get(settings.OIDC_OP_USER_ENDPOINT, text=json.dumps(userinfo))

    request = rf.get("/openid", HTTP_AUTHORIZATION="Bearer Token")

    try:
        user, _ = OIDCAuthentication().authenticate(request)
    except AuthenticationFailed:
        assert not create_user
    else:
        assert user.username == username

    assert user_model.objects.count() == expected_count


@pytest.mark.django_db()
def test_authentication_update_user_data(rf, requests_mock, settings):
    user_model = get_user_model()
    user = UserFactory.create()

    userinfo = {
        "sub": user.username,
        "email": "test@localhost",
        "given_name": "Max",
        "family_name": "Mustermann",
    }

    requests_mock.get(settings.OIDC_OP_USER_ENDPOINT, text=json.dumps(userinfo))

    request = rf.get("/openid", HTTP_AUTHORIZATION="Bearer Token")

    user, _ = OIDCAuthentication().authenticate(request)

    assert user_model.objects.count() == 1
    assert user.first_name == "Max"
    assert user.last_name == "Mustermann"
    assert user.email == "test@localhost"


@pytest.mark.django_db()
def test_authentication_idp_502(rf, requests_mock, settings):
    requests_mock.get(
        settings.OIDC_OP_USER_ENDPOINT, status_code=status.HTTP_502_BAD_GATEWAY
    )

    request = rf.get("/openid", HTTP_AUTHORIZATION="Bearer Token")
    with pytest.raises(HTTPError):
        OIDCAuthentication().authenticate(request)


@pytest.mark.django_db()
def test_authentication_idp_missing_claim(rf, requests_mock, settings):
    settings.OIDC_USERNAME_CLAIM = "missing"
    userinfo = {"preferred_username": "1"}
    requests_mock.get(settings.OIDC_OP_USER_ENDPOINT, text=json.dumps(userinfo))

    request = rf.get("/openid", HTTP_AUTHORIZATION="Bearer Token")
    with pytest.raises(AuthenticationFailed):
        OIDCAuthentication().authenticate(request)


@pytest.mark.django_db()
def test_authentication_no_client(rf, requests_mock, settings):
    requests_mock.get(
        settings.OIDC_OP_USER_ENDPOINT, status_code=status.HTTP_401_UNAUTHORIZED
    )
    requests_mock.post(
        settings.OIDC_OP_INTROSPECT_ENDPOINT,
        text=json.dumps({"preferred_username": "1"}),
    )

    request = rf.get("/openid", HTTP_AUTHORIZATION="Bearer Token")
    with pytest.raises(AuthenticationFailed):
        OIDCAuthentication().authenticate(request)


@pytest.mark.django_db()
@pytest.mark.parametrize("check_introspect", [True, False])
def test_userinfo_introspection_failure(
    client, rf, requests_mock, settings, check_introspect
):
    settings.OIDC_CHECK_INTROSPECT = check_introspect
    requests_mock.get(
        settings.OIDC_OP_USER_ENDPOINT, status_code=status.HTTP_401_UNAUTHORIZED
    )
    requests_mock.post(
        settings.OIDC_OP_INTROSPECT_ENDPOINT, status_code=status.HTTP_403_FORBIDDEN
    )
    resp = client.get(reverse("user-me"), HTTP_AUTHORIZATION="Bearer Token")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    request = rf.get("/openid", HTTP_AUTHORIZATION="Bearer Token")
    with pytest.raises(AuthenticationFailed):
        OIDCAuthentication().authenticate(request)
    cache.clear()
