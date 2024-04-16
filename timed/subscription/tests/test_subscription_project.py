from datetime import timedelta

import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from timed.employment.factories import EmploymentFactory
from timed.projects.factories import (
    BillingTypeFactory,
    CustomerAssigneeFactory,
    CustomerFactory,
    ProjectFactory,
    TaskFactory,
)
from timed.subscription.factories import OrderFactory, PackageFactory
from timed.tracking.factories import ReportFactory


@pytest.mark.parametrize(("is_external", "expected"), [(True, 0), (False, 1)])
def test_subscription_project_list(auth_client, is_external, expected):
    employment = EmploymentFactory.create(user=auth_client.user, is_external=False)
    if is_external:
        employment.is_external = True
        employment.save()
    customer = CustomerFactory.create()
    billing_type = BillingTypeFactory()
    project = ProjectFactory.create(
        billing_type=billing_type, customer=customer, customer_visible=True
    )
    PackageFactory.create_batch(2, billing_type=billing_type)
    # create spent hours
    task = TaskFactory.create(project=project)
    TaskFactory.create(project=project)
    ReportFactory.create(task=task, duration=timedelta(hours=2))
    ReportFactory.create(task=task, duration=timedelta(hours=3))
    # not billable reports should not be included in spent hours
    ReportFactory.create(not_billable=True, task=task, duration=timedelta(hours=4))
    # project of same customer but without customer_visible set
    # should not appear
    ProjectFactory.create(customer=customer)

    # create purchased time
    OrderFactory.create(project=project, acknowledged=True, duration=timedelta(hours=2))
    OrderFactory.create(project=project, acknowledged=True, duration=timedelta(hours=4))

    # report on different project should not be included in spent time
    ReportFactory.create(duration=timedelta(hours=2))
    # not acknowledged order should not be included in purchased time
    OrderFactory.create(project=project, duration=timedelta(hours=2))

    url = reverse("subscription-project-list")

    res = auth_client.get(url, data={"customer": customer.id, "ordering": "id"})
    assert res.status_code == HTTP_200_OK

    json = res.json()
    assert len(json["data"]) == expected
    if expected:
        assert json["data"][0]["id"] == str(project.id)

        attrs = json["data"][0]["attributes"]
        assert attrs["spent-time"] == "05:00:00"
        assert attrs["purchased-time"] == "06:00:00"


@pytest.mark.parametrize(
    ("is_customer", "project_of_customer", "has_employment", "is_external", "expected"),
    [
        (True, True, False, False, HTTP_200_OK),
        (True, False, False, False, HTTP_404_NOT_FOUND),
        (False, False, True, False, HTTP_200_OK),
        (False, False, True, True, HTTP_404_NOT_FOUND),
    ],
)
def test_subscription_project_detail(
    auth_client, is_customer, project_of_customer, has_employment, is_external, expected
):
    user = auth_client.user
    billing_type = BillingTypeFactory()
    project = ProjectFactory.create(billing_type=billing_type, customer_visible=True)
    PackageFactory.create_batch(2, billing_type=billing_type)

    if has_employment:
        employment = EmploymentFactory.create(user=user, is_external=False)
        if is_external:
            employment.is_external = True
            employment.save()

    if is_customer:
        customer_assignee = CustomerAssigneeFactory(user=user, is_customer=True)
        if project_of_customer:
            customer_assignee.customer = project.customer
            customer_assignee.save()

    url = reverse("subscription-project-detail", args=[project.id])
    res = auth_client.get(url)
    assert res.status_code == expected

    if expected == HTTP_200_OK:
        json = res.json()
        assert json["data"]["id"] == str(project.id)


def test_subscription_project_list_user_is_customer(auth_client):
    customer = CustomerFactory.create()
    project = ProjectFactory.create(customer=customer, customer_visible=True)
    ProjectFactory.create_batch(4, customer_visible=True)

    user = auth_client.user
    CustomerAssigneeFactory.create(user=user, customer=customer, is_customer=True)

    url = reverse("subscription-project-list")

    response = auth_client.get(url)
    assert response.status_code == HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(project.id)
    assert json["data"][0]["relationships"]["customer"]["data"]["id"] == str(
        customer.id
    )
