"""Tests for the tasks endpoint."""
from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status

from timed.projects.factories import TaskFactory
from timed.tracking.factories import ReportFactory


def test_task_list_not_archived(auth_client):
    task = TaskFactory.create(archived=False)
    TaskFactory.create(archived=True)
    url = reverse("task-list")

    response = auth_client.get(url, data={"archived": 0})
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(task.id)


def test_task_my_most_frequent(auth_client):
    user = auth_client.user
    tasks = TaskFactory.create_batch(6)

    report_date = date.today() - timedelta(days=20)
    old_report_date = date.today() - timedelta(days=90)

    # tasks[0] should appear as most frequently used task
    ReportFactory.create_batch(5, date=report_date, user=user, task=tasks[0])
    # tasks[1] should appear as secondly most frequently used task
    ReportFactory.create_batch(4, date=report_date, user=user, task=tasks[1])
    # tasks[2] should not appear in result, as too far in the past
    ReportFactory.create_batch(4, date=old_report_date, user=user, task=tasks[2])
    # tasks[3] should not appear in result, as project is archived
    tasks[3].project.archived = True
    tasks[3].project.save()
    ReportFactory.create_batch(4, date=report_date, user=user, task=tasks[3])
    # tasks[4] should not appear in result, as task is archived
    tasks[4].archived = True
    tasks[4].save()
    ReportFactory.create_batch(4, date=report_date, user=user, task=tasks[4])

    url = reverse("task-list")

    response = auth_client.get(url, {"my_most_frequent": "10"})
    assert response.status_code == status.HTTP_200_OK

    data = response.json()["data"]
    assert len(data) == 2
    assert data[0]["id"] == str(tasks[0].id)
    assert data[1]["id"] == str(tasks[1].id)


def test_task_detail(auth_client):
    task = TaskFactory.create()

    url = reverse("task-detail", args=[task.id])

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK


def test_task_create(auth_client):
    url = reverse("task-list")

    response = auth_client.post(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_task_update(auth_client):
    task = TaskFactory.create()

    url = reverse("task-detail", args=[task.id])

    response = auth_client.patch(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_task_delete(auth_client):
    task = TaskFactory.create()

    url = reverse("task-detail", args=[task.id])

    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_task_detail_no_reports(auth_client):
    task = TaskFactory.create()

    url = reverse("task-detail", args=[task.id])

    res = auth_client.get(url)

    assert res.status_code == status.HTTP_200_OK

    json = res.json()
    assert json["meta"]["spent-time"] == "00:00:00"


def test_task_detail_with_reports(auth_client):
    task = TaskFactory.create()
    ReportFactory.create_batch(5, task=task, duration=timedelta(minutes=30))

    url = reverse("task-detail", args=[task.id])

    res = auth_client.get(url)

    assert res.status_code == status.HTTP_200_OK

    json = res.json()
    assert json["meta"]["spent-time"] == "02:30:00"
