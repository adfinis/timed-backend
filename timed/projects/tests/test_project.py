"""Tests for the projects endpoint."""
from datetime import timedelta

from django.urls import reverse
from rest_framework import status

from timed.employment.factories import EmploymentFactory, UserFactory
from timed.projects.factories import ProjectFactory
from timed.projects.serializers import ProjectSerializer


def test_project_list_not_archived(auth_client):
    project = ProjectFactory.create(archived=False)
    ProjectFactory.create(archived=True)

    url = reverse("project-list")

    response = auth_client.get(url, data={"archived": 0})
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(project.id)


def test_project_list_include(auth_client, django_assert_num_queries, project):
    users = UserFactory.create_batch(2)
    project.reviewers.add(*users)

    url = reverse("project-list")

    with django_assert_num_queries(16):
        response = auth_client.get(
            url,
            data={"include": ",".join(ProjectSerializer.included_serializers.keys())},
        )
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(project.id)


def test_project_detail_no_auth(db, client, project):
    url = reverse("project-detail", args=[project.id])

    res = client.get(url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_project_detail_no_reports(auth_client, project):
    url = reverse("project-detail", args=[project.id])

    res = auth_client.get(url)

    assert res.status_code == status.HTTP_200_OK
    json = res.json()

    assert json["meta"]["spent-time"] == "00:00:00"
    assert json["meta"]["spent-billable"] == "00:00:00"


def test_project_detail_with_reports(auth_client, project, task, report_factory):
    rep1, rep2, rep3, *_ = report_factory.create_batch(
        10, task=task, duration=timedelta(hours=1)
    )
    rep1.not_billable = True
    rep1.save()
    rep2.review = True
    rep2.save()
    rep3.not_billable = True
    rep3.review = True
    rep3.save()

    url = reverse("project-detail", args=[project.id])

    res = auth_client.get(url)

    assert res.status_code == status.HTTP_200_OK
    json = res.json()

    assert json["meta"]["spent-time"] == "10:00:00"
    assert json["meta"]["spent-billable"] == "07:00:00"


def test_project_create(auth_client):
    url = reverse("project-list")

    response = auth_client.post(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_project_update(auth_client, project):
    url = reverse("project-detail", args=[project.id])

    response = auth_client.patch(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_project_delete(auth_client, project):
    url = reverse("project-detail", args=[project.id])

    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_project_list_external_user(auth_client):
    EmploymentFactory.create(user=auth_client.user, is_external=True)
    project = ProjectFactory.create()
    project.assignees.add(auth_client.user)
    ProjectFactory.create_batch(4)

    url = reverse("project-list")

    response = auth_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
