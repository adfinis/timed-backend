import io
from datetime import date
from zipfile import ZipFile

import ezodf
import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from timed.projects.factories import (CustomerFactory, ProjectFactory,
                                      TaskFactory)
from timed.reports.views import WorkReportViewSet
from timed.tracking.factories import ReportFactory


@pytest.mark.freeze_time('2017-09-01')
def test_work_report_single_project(auth_client, django_assert_num_queries):
    user = auth_client.user
    # spaces should be replaced with underscore
    customer = CustomerFactory.create(name='Customer Name')
    # slashes should be dropped from file name
    project = ProjectFactory.create(customer=customer, name='Project/')
    task = TaskFactory.create(project=project)
    ReportFactory.create_batch(
        10, user=user, verified_by=user, task=task, date=date(2017, 8, 17)
    )

    url = reverse('work-report-list')
    with django_assert_num_queries(4):
        res = auth_client.get(url, data={
            'user': auth_client.user.id,
            'from_date': '2017-08-01',
            'to_date': '2017-08-31',
            'verified': 1
        })
    assert res.status_code == HTTP_200_OK
    assert '1708-20170901-Customer_Name-Project.ods' in (
        res['Content-Disposition']
    )

    content = io.BytesIO(res.content)
    doc = ezodf.opendoc(content)
    table = doc.sheets[0]
    assert table['C5'].value == '2017-08-01'
    assert table['C6'].value == '2017-08-31'
    assert table['C9'].value == 'Test User'
    assert table['C10'].value == 'Test User'


@pytest.mark.freeze_time('2017-09-01')
def test_work_report_multiple_projects(auth_client, django_assert_num_queries):
    NUM_PROJECTS = 2

    user = auth_client.user
    customer = CustomerFactory.create(name='Customer')
    report_date = date(2017, 8, 17)
    for i in range(NUM_PROJECTS):
        project = ProjectFactory.create(
            customer=customer, name='Project{0}'.format(i)
        )
        task = TaskFactory.create(project=project)
        ReportFactory.create_batch(10, user=user, task=task, date=report_date)

    url = reverse('work-report-list')
    with django_assert_num_queries(4):
        res = auth_client.get(url, data={
            'user': auth_client.user.id,
            'verified': 0
        })
    assert res.status_code == HTTP_200_OK
    assert '20170901-WorkReports.zip' in (
        res['Content-Disposition']
    )

    content = io.BytesIO(res.content)
    with ZipFile(content, 'r') as zipfile:
        for i in range(NUM_PROJECTS):
            ods_content = zipfile.read(
                '1708-20170901-Customer-Project{0}.ods'.format(i)
            )
            doc = ezodf.opendoc(io.BytesIO(ods_content))
            table = doc.sheets[0]
            assert table['C5'].value == '2017-08-17'
            assert table['C6'].value == '2017-08-17'


def test_work_report_empty(auth_client):
    url = reverse('work-report-list')
    res = auth_client.get(url, data={
        'user': auth_client.user.id
    })
    assert res.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.parametrize('customer_name,project_name,expected', [
    ('Customer Name', 'Project/', '1708-20170818-Customer_Name-Project.ods'),
    ('Customer-Name', 'Project', '1708-20170818-Customer-Name-Project.ods'),
    ('Customer$Name', 'Project', '1708-20170818-CustomerName-Project.ods'),
])
def test_generate_work_report_name(db, customer_name, project_name, expected):
    test_date = date(2017, 8, 18)
    view = WorkReportViewSet()

    # spaces should be replaced with underscore
    customer = CustomerFactory.create(name=customer_name)
    # slashes should be dropped from file name
    project = ProjectFactory.create(customer=customer, name=project_name)

    name = view._generate_workreport_name(test_date, test_date, project)
    assert name == expected
