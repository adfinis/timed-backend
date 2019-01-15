import environ
import pytest

from timed import settings


def test_admins():
    assert settings.parse_admins(["Test Example <test@example.com>"]) == [
        ("Test Example", "test@example.com")
    ]


def test_invalid_admins(monkeypatch):
    with pytest.raises(environ.ImproperlyConfigured):
        settings.parse_admins(["Test Example <test@example.com"])
