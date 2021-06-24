import inspect

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from factory.base import FactoryMetaClass
from pytest_factoryboy import register
from rest_framework.test import APIClient

from timed.employment import factories as employment_factories
from timed.projects import factories as projects_factories
from timed.subscription import factories as subscription_factories
from timed.tracking import factories as tracking_factories


def register_module(module):
    for name, obj in inspect.getmembers(module):
        if isinstance(obj, FactoryMetaClass) and not obj._meta.abstract:
            register(obj)


register_module(employment_factories)
register_module(projects_factories)
register_module(subscription_factories)
register_module(tracking_factories)


@pytest.fixture
def auth_user(db):
    return get_user_model().objects.create_user(
        username="user",
        password="123qweasd",
        first_name="Test",
        last_name="User",
        is_superuser=False,
        is_staff=False,
    )


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_user(
        username="admin",
        password="123qweasd",
        first_name="Admin",
        last_name="User",
        is_superuser=False,
        is_staff=True,
    )


@pytest.fixture
def superadmin_user(db):
    return get_user_model().objects.create_user(
        username="superadmin",
        password="123qweasd",
        first_name="Superadmin",
        last_name="User",
        is_superuser=True,
        is_staff=True,
    )


@pytest.fixture
def external_employee(db):
    user = get_user_model().objects.create_user(
        username="user",
        password="123qweasd",
        first_name="Test",
        last_name="User",
        is_superuser=False,
        is_staff=False,
    )
    employment_factories.EmploymentFactory.create(user=user, is_external=True)
    return user


@pytest.fixture
def internal_employee(db):
    user = get_user_model().objects.create_user(
        username="user",
        password="123qweasd",
        first_name="Test",
        last_name="User",
        is_superuser=False,
        is_staff=False,
    )
    employment_factories.EmploymentFactory.create(user=user, is_external=False)
    return user


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(auth_user):
    """Return instance of a APIClient that is logged in as test user."""
    client = APIClient()
    client.force_authenticate(user=auth_user)
    client.user = auth_user
    return client


@pytest.fixture
def admin_client(admin_user):
    """Return instance of a APIClient that is logged in as a staff user."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    client.user = admin_user
    return client


@pytest.fixture
def superadmin_client(superadmin_user):
    """Return instance of a APIClient that is logged in as superuser."""
    client = APIClient()
    client.force_authenticate(user=superadmin_user)
    client.user = superadmin_user
    return client


@pytest.fixture
def external_employee_client(external_employee):
    """Return instance of a APIClient that is logged in as external test user."""
    client = APIClient()
    client.force_authenticate(user=external_employee)
    client.user = external_employee
    return client


@pytest.fixture
def internal_employee_client(internal_employee):
    """Return instance of a APIClient that is logged in as external test user."""
    client = APIClient()
    client.force_authenticate(user=internal_employee)
    client.user = internal_employee
    return client


@pytest.fixture(scope="function", autouse=True)
def _autoclear_cache():
    cache.clear()
