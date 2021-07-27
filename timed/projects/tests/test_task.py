"""Tests for the tasks endpoint."""
from datetime import date, timedelta

import pytest
from django.urls import reverse
from rest_framework import status

from timed.employment.factories import EmploymentFactory
from timed.projects.factories import ProjectFactory, TaskFactory


def test_task_list_not_archived(internal_employee_client, task_factory):
    task = task_factory(archived=False)
    task_factory(archived=True)
    url = reverse("task-list")

    response = internal_employee_client.get(url, data={"archived": 0})
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(task.id)


def test_task_my_most_frequent(internal_employee_client, task_factory, report_factory):
    user = internal_employee_client.user
    tasks = task_factory.create_batch(6)

    report_date = date.today() - timedelta(days=20)
    old_report_date = date.today() - timedelta(days=90)

    # tasks[0] should appear as most frequently used task
    report_factory.create_batch(5, date=report_date, user=user, task=tasks[0])
    # tasks[1] should appear as secondly most frequently used task
    report_factory.create_batch(4, date=report_date, user=user, task=tasks[1])
    # tasks[2] should not appear in result, as too far in the past
    report_factory.create_batch(4, date=old_report_date, user=user, task=tasks[2])
    # tasks[3] should not appear in result, as project is archived
    tasks[3].project.archived = True
    tasks[3].project.save()
    report_factory.create_batch(4, date=report_date, user=user, task=tasks[3])
    # tasks[4] should not appear in result, as task is archived
    tasks[4].archived = True
    tasks[4].save()
    report_factory.create_batch(4, date=report_date, user=user, task=tasks[4])

    url = reverse("task-list")

    response = internal_employee_client.get(url, {"my_most_frequent": "10"})
    assert response.status_code == status.HTTP_200_OK

    data = response.json()["data"]
    assert len(data) == 2
    assert data[0]["id"] == str(tasks[0].id)
    assert data[1]["id"] == str(tasks[1].id)


def test_task_detail(internal_employee_client, task):
    url = reverse("task-detail", args=[task.id])

    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "project_assignee__is_resource, project_assignee__is_manager, project_assignee__is_reviewer, customer_assignee__is_manager, expected",
    [
        (True, False, False, False, status.HTTP_403_FORBIDDEN),
        (False, True, False, False, status.HTTP_201_CREATED),
        (False, False, True, False, status.HTTP_403_FORBIDDEN),
        (False, False, False, True, status.HTTP_201_CREATED),
    ],
)
def test_task_create(
    auth_client, project, project_assignee, customer_assignee, expected
):
    user = auth_client.user
    project_assignee.user = user
    project_assignee.save()
    if customer_assignee.is_manager:
        customer_assignee.customer = project.customer
        customer_assignee.user = user
        customer_assignee.save()

    url = reverse("task-list")

    data = {
        "data": {
            "attributes": {"name": "test task"},
            "relationships": {
                "project": {"data": {"type": "projects", "id": project.pk}}
            },
            "type": "tasks",
        }
    }
    response = auth_client.post(url, data=data)
    assert response.status_code == expected


@pytest.mark.parametrize(
    "task_assignee__is_resource, task_assignee__is_manager, task_assignee__is_reviewer, project_assignee__is_reviewer, project_assignee__is_manager, different_project, expected",
    [
        (True, False, False, False, False, False, status.HTTP_403_FORBIDDEN),
        (False, True, False, False, False, False, status.HTTP_200_OK),
        (False, False, True, False, False, False, status.HTTP_403_FORBIDDEN),
        (False, False, False, True, False, False, status.HTTP_403_FORBIDDEN),
        (False, False, False, False, True, False, status.HTTP_200_OK),
        (False, False, False, False, True, True, status.HTTP_403_FORBIDDEN),
    ],
)
def test_task_update(
    auth_client, task, task_assignee, project_assignee, different_project, expected
):
    user = auth_client.user
    EmploymentFactory.create(user=user)
    task_assignee.task = task
    task_assignee.user = user
    task_assignee.save()
    if different_project:
        project = ProjectFactory.create()
        project_assignee.project = project
    project_assignee.user = user
    project_assignee.save()

    data = {
        "data": {
            "type": "tasks",
            "id": task.id,
            "attributes": {"name": "Test Task"},
        }
    }

    url = reverse("task-detail", args=[task.id])

    response = auth_client.patch(url, data)
    assert response.status_code == expected


@pytest.mark.parametrize(
    "project_assignee__is_resource, project_assignee__is_manager, project_assignee__is_reviewer, expected",
    [
        (True, False, False, status.HTTP_403_FORBIDDEN),
        (False, True, False, status.HTTP_204_NO_CONTENT),
        (False, False, True, status.HTTP_403_FORBIDDEN),
    ],
)
def test_task_delete(auth_client, task, project_assignee, expected):
    user = auth_client.user
    project_assignee.project = task.project
    project_assignee.user = user
    project_assignee.save()
    EmploymentFactory.create(user=user)

    url = reverse("task-detail", args=[task.id])

    response = auth_client.delete(url)
    assert response.status_code == expected


def test_task_detail_no_reports(internal_employee_client, task):
    url = reverse("task-detail", args=[task.id])

    res = internal_employee_client.get(url)

    assert res.status_code == status.HTTP_200_OK

    json = res.json()
    assert json["meta"]["spent-time"] == "00:00:00"


def test_task_detail_with_reports(internal_employee_client, task, report_factory):
    report_factory.create_batch(5, task=task, duration=timedelta(minutes=30))

    url = reverse("task-detail", args=[task.id])

    res = internal_employee_client.get(url)

    assert res.status_code == status.HTTP_200_OK

    json = res.json()
    assert json["meta"]["spent-time"] == "02:30:00"


@pytest.mark.parametrize("is_assigned, expected", [(True, 1), (False, 0)])
def test_task_list_external_employee(external_employee_client, is_assigned, expected):
    TaskFactory.create_batch(4)
    task = TaskFactory.create()
    if is_assigned:
        task.assignees.add(external_employee_client.user)

    url = reverse("task-list")

    response = external_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == expected
