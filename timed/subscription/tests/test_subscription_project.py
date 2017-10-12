from datetime import timedelta

from django.core.urlresolvers import reverse
from rest_framework.status import HTTP_200_OK

from timed.projects.factories import (BillingTypeFactory, CustomerFactory,
                                      ProjectFactory, TaskFactory)
from timed.subscription.factories import OrderFactory, PackageFactory
from timed.tracking.factories import ReportFactory


def test_subscription_project_list(auth_client):
    customer = CustomerFactory.create()
    billing_type = BillingTypeFactory()
    project = ProjectFactory.create(
        billing_type=billing_type,
        customer=customer
    )
    PackageFactory.create(billing_type=billing_type)
    # create spent hours
    task = TaskFactory.create(project=project)
    TaskFactory.create(project=project)
    ReportFactory.create(task=task, duration=timedelta(hours=2))
    ReportFactory.create(task=task, duration=timedelta(hours=3))
    # not billable reports should not be included in spent hours
    ReportFactory.create(not_billable=True, task=task,
                         duration=timedelta(hours=4))
    # project of same customer but without a billing type with packages
    # should not appear
    ProjectFactory.create(customer=customer)

    # create purchased time
    OrderFactory.create(
        project=project,
        acknowledged=True,
        duration=timedelta(hours=2)
    )
    OrderFactory.create(
        project=project,
        acknowledged=True,
        duration=timedelta(hours=4)
    )

    # report on different project should not be included in spent time
    ReportFactory.create(duration=timedelta(hours=2))
    # not acknowledged order should not be included in purchased time
    OrderFactory.create(
        project=project,
        duration=timedelta(hours=2)
    )

    url = reverse('subscription-project-list')

    res = auth_client.get(
        url,
        data={'customer': customer.id,
              'ordering': 'id'}
    )
    assert res.status_code == HTTP_200_OK

    json = res.json()
    assert len(json['data']) == 1
    assert json['data'][0]['id'] == str(project.id)

    attrs = json['data'][0]['attributes']
    assert attrs['spent-time'] == '05:00:00'
    assert attrs['purchased-time'] == '06:00:00'
