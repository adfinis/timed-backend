import io
from datetime import date
from zipfile import ZipFile

import ezodf
import pytest
from django.urls import reverse
from rest_framework import status

from timed.conftest import setup_customer_and_employment_status
from timed.employment.factories import EmploymentFactory
from timed.projects.factories import CustomerFactory, ProjectFactory, TaskFactory
from timed.reports.views import WorkReportViewSet
from timed.tracking.factories import ReportFactory


@pytest.mark.freeze_time("2017-09-01")
@pytest.mark.parametrize(
    ("is_employed", "is_customer_assignee", "is_customer", "expected", "status_code"),
    [
        (False, True, False, 1, status.HTTP_400_BAD_REQUEST),
        (False, True, True, 1, status.HTTP_400_BAD_REQUEST),
        (True, False, False, 4, status.HTTP_200_OK),
        (True, True, False, 4, status.HTTP_200_OK),
        (True, True, True, 4, status.HTTP_200_OK),
    ],
)
def test_work_report_single_project(
    auth_client,
    is_employed,
    is_customer_assignee,
    is_customer,
    expected,
    status_code,
    django_assert_num_queries,
):
    user = auth_client.user
    setup_customer_and_employment_status(
        user=user,
        is_assignee=is_customer_assignee,
        is_customer=is_customer,
        is_employed=is_employed,
        is_external=False,
    )
    # spaces should be replaced with underscore
    customer = CustomerFactory.create(name="Customer Name")
    # slashes should be dropped from file name
    project = ProjectFactory.create(customer=customer, name="Project/")
    task = TaskFactory.create(project=project)
    ReportFactory.create_batch(
        5,
        user=user,
        verified_by=user,
        task=task,
        date=date(2017, 8, 17),
        not_billable=True,
    )
    ReportFactory.create_batch(
        5,
        user=user,
        verified_by=user,
        task=task,
        date=date(2017, 8, 17),
        not_billable=False,
    )

    url = reverse("work-report-list")
    with django_assert_num_queries(expected):
        res = auth_client.get(
            url,
            data={
                "user": auth_client.user.id,
                "from_date": "2017-08-01",
                "to_date": "2017-08-31",
                "verified": 1,
            },
        )
    assert res.status_code == status_code

    if status_code == status.HTTP_200_OK:
        assert "1708-20170901-Customer_Name-Project.ods" in (res["Content-Disposition"])

        content = io.BytesIO(res.content)
        doc = ezodf.opendoc(content)
        table = doc.sheets[0]
        assert table["C5"].value == "2017-08-01"
        assert table["C6"].value == "2017-08-31"
        assert table["C9"].value == "Test User"
        assert table["C10"].value == "Test User"


@pytest.mark.freeze_time("2017-09-01")
@pytest.mark.parametrize(
    ("is_employed", "status_code", "expected"),
    [
        (True, status.HTTP_200_OK, 3),
        (False, status.HTTP_400_BAD_REQUEST, 1),
    ],
)
def test_work_report_multiple_projects(
    auth_client, is_employed, status_code, expected, django_assert_num_queries
):
    num_projects = 2

    user = auth_client.user
    if is_employed:
        EmploymentFactory.create(user=user)
    customer = CustomerFactory.create(name="Customer")
    report_date = date(2017, 8, 17)
    for i in range(num_projects):
        project = ProjectFactory.create(customer=customer, name=f"Project{i}")
        task = TaskFactory.create(project=project)
        ReportFactory.create_batch(10, user=user, task=task, date=report_date)

    url = reverse("work-report-list")
    with django_assert_num_queries(expected):
        res = auth_client.get(url, data={"user": auth_client.user.id, "verified": 0})
    assert res.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert "20170901-WorkReports.zip" in (res["Content-Disposition"])

        content = io.BytesIO(res.content)
        with ZipFile(content, "r") as zipfile:
            for i in range(num_projects):
                ods_content = zipfile.read(f"1708-20170901-Customer-Project{i}.ods")
                doc = ezodf.opendoc(io.BytesIO(ods_content))
                table = doc.sheets[0]
                assert table["C5"].value == "2017-08-17"
                assert table["C6"].value == "2017-08-17"


def test_work_report_empty(auth_client):
    url = reverse("work-report-list")
    res = auth_client.get(url, data={"user": auth_client.user.id})
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.freeze_time("2017-08-18")
@pytest.mark.django_db()
@pytest.mark.parametrize(
    ("customer_name", "project_name", "expected"),
    [
        ("Customer Name", "Project/", "1708-20170818-Customer_Name-Project.ods"),
        ("Customer-Name", "Project", "1708-20170818-Customer-Name-Project.ods"),
        ("Customer$Name", "Project", "1708-20170818-CustomerName-Project.ods"),
    ],
)
def test_generate_work_report_name(customer_name, project_name, expected):
    test_date = date(2017, 8, 18)
    view = WorkReportViewSet()

    # spaces should be replaced with underscore
    customer = CustomerFactory.create(name=customer_name)
    # slashes should be dropped from file name
    project = ProjectFactory.create(customer=customer, name=project_name)

    name = view._generate_workreport_name(test_date, project)  # noqa: SLF001
    assert name == expected


@pytest.mark.freeze_time("2017-09-01")
@pytest.mark.parametrize(
    ("settings_count", "given_count", "expected_status"),
    [
        (-1, 9, status.HTTP_200_OK),
        (0, 9, status.HTTP_200_OK),
        (10, 9, status.HTTP_200_OK),
        (9, 10, status.HTTP_400_BAD_REQUEST),
    ],
)
def test_work_report_count(
    internal_employee_client, settings, settings_count, given_count, expected_status
):
    user = internal_employee_client.user
    customer = CustomerFactory.create(name="Customer")
    report_date = date(2017, 8, 17)

    settings.WORK_REPORTS_EXPORT_MAX_COUNT = settings_count

    project = ProjectFactory.create(customer=customer)
    task = TaskFactory.create(project=project)
    ReportFactory.create_batch(given_count, user=user, task=task, date=report_date)

    url = reverse("work-report-list")
    res = internal_employee_client.get(
        url, data={"user": internal_employee_client.user.id, "verified": 0}
    )

    assert res.status_code == expected_status
