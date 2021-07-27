"""Tests for the reports endpoint."""

from datetime import timedelta

import pyexcel
import pytest
from django.urls import reverse
from django.utils.duration import duration_string
from rest_framework import status

from timed.employment.factories import EmploymentFactory, UserFactory
from timed.projects.factories import TaskAssigneeFactory


def test_report_list(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report_factory.create(user=user)
    report = report_factory.create(user=user, duration=timedelta(hours=1))
    url = reverse("report-list")

    response = internal_employee_client.get(
        url,
        data={
            "date": report.date,
            "user": user.id,
            "task": report.task_id,
            "project": report.task.project_id,
            "customer": report.task.project.customer_id,
            "include": ("user,task,task.project,task.project.customer,verified_by"),
        },
    )

    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(report.id)
    assert json["meta"]["total-time"] == "01:00:00"


def test_report_intersection_full(
    internal_employee_client,
    report_factory,
):
    report = report_factory.create()

    url = reverse("report-intersection")
    response = internal_employee_client.get(
        url,
        data={
            "ordering": "task__name",
            "task": report.task.id,
            "project": report.task.project.id,
            "customer": report.task.project.customer.id,
            "include": "task,customer,project",
        },
    )
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    pk = json["data"].pop("id")
    assert "task={0}".format(report.task.id) in pk
    assert "project={0}".format(report.task.project.id) in pk
    assert "customer={0}".format(report.task.project.customer.id) in pk

    included = json.pop("included")
    assert len(included) == 3

    expected = {
        "data": {
            "type": "report-intersections",
            "attributes": {
                "comment": report.comment,
                "not-billable": False,
                "verified": False,
                "review": False,
                "billed": False,
            },
            "relationships": {
                "customer": {
                    "data": {
                        "id": str(report.task.project.customer.id),
                        "type": "customers",
                    }
                },
                "project": {
                    "data": {"id": str(report.task.project.id), "type": "projects"}
                },
                "task": {"data": {"id": str(report.task.id), "type": "tasks"}},
            },
        },
        "meta": {"count": 1},
    }
    assert json == expected


def test_report_intersection_partial(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create(review=True, not_billable=True, comment="test")
    report_factory.create(verified_by=user, comment="test")
    # Billed is not set on create because the factory doesnt seem to work with that
    report.billed = True
    report.save()

    url = reverse("report-intersection")
    response = internal_employee_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    expected = {
        "data": {
            "id": "",
            "type": "report-intersections",
            "attributes": {
                "comment": "test",
                "not-billable": None,
                "verified": None,
                "review": None,
                "billed": None,
            },
            "relationships": {
                "customer": {"data": None},
                "project": {"data": None},
                "task": {"data": None},
            },
        },
        "meta": {"count": 2},
    }
    assert json == expected


def test_report_list_filter_id(
    internal_employee_client,
    report_factory,
):
    report_1 = report_factory.create(date="2017-01-01")
    report_2 = report_factory.create(date="2017-02-01")
    report_factory.create()

    url = reverse("report-list")

    response = internal_employee_client.get(
        url, data={"id": "{0},{1}".format(report_1.id, report_2.id), "ordering": "id"}
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 2
    assert json["data"][0]["id"] == str(report_1.id)
    assert json["data"][1]["id"] == str(report_2.id)


def test_report_list_filter_id_empty(
    internal_employee_client,
    report_factory,
):
    """Test that empty id filter is ignored."""
    report_factory.create()

    url = reverse("report-list")

    response = internal_employee_client.get(url, data={"id": ""})
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1


def test_report_list_filter_reviewer(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create(user=user)
    report.task.project.reviewers.add(user)

    url = reverse("report-list")

    response = internal_employee_client.get(url, data={"reviewer": user.id})
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(report.id)


def test_report_list_filter_verifier(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create(verified_by=user)
    report_factory.create()

    url = reverse("report-list")

    response = internal_employee_client.get(url, data={"verifier": user.id})
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(report.id)


def test_report_list_filter_editable_owner(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create(user=user)
    report_factory.create()

    url = reverse("report-list")

    response = internal_employee_client.get(url, data={"editable": 1})
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(report.id)


def test_report_list_filter_not_editable_owner(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report_factory.create(user=user)
    report = report_factory.create()

    url = reverse("report-list")

    response = internal_employee_client.get(url, data={"editable": 0})
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(report.id)


def test_report_list_filter_editable_reviewer(
    internal_employee_client, report_factory, user_factory
):
    user = internal_employee_client.user
    # not editable report
    report_factory.create()

    # editable reports
    # 1st report of current user
    report_factory.create(user=user)
    # 2nd case: report of a project which has several
    # reviewers and report is created by current user
    report = report_factory.create(user=user)
    other_user = user_factory.create()
    report.task.project.reviewers.add(user)
    report.task.project.reviewers.add(other_user)
    # 3rd case: report by other user and current user
    # is the reviewer
    reviewer_report = report_factory.create()
    reviewer_report.task.project.reviewers.add(user)

    url = reverse("report-list")

    response = internal_employee_client.get(url, data={"editable": 1})
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 3


def test_report_list_filter_editable_superuser(superadmin_client, report_factory):
    EmploymentFactory.create(user=superadmin_client.user)
    report = report_factory.create()

    url = reverse("report-list")

    response = superadmin_client.get(url, data={"editable": 1})
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(report.id)


def test_report_list_filter_not_editable_superuser(superadmin_client, report_factory):
    EmploymentFactory.create(user=superadmin_client.user)
    report_factory.create()

    url = reverse("report-list")

    response = superadmin_client.get(url, data={"editable": 0})
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 0


def test_report_list_filter_editable_supervisor(
    internal_employee_client,
    report_factory,
    user_factory,
):
    user = internal_employee_client.user
    # not editable report
    report_factory.create()

    # editable reports
    # 1st case: report by current user
    report_factory.create(user=user)
    # 2nd case: report by current user with several supervisors
    report = report_factory.create(user=user)
    report.user.supervisors.add(user)
    other_user = user_factory.create()
    report.user.supervisors.add(other_user)
    # 3rd case: report by different user with current user as supervisor
    supervisor_report = report_factory.create()
    supervisor_report.user.supervisors.add(user)

    url = reverse("report-list")

    response = internal_employee_client.get(url, data={"editable": 1})
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 3


def test_report_list_filter_billed(
    internal_employee_client,
    report,
):
    # Billed is not set on create because the factory doesnt seem to work with that
    report.billed = True
    report.save()

    url = reverse("report-list")

    response = internal_employee_client.get(url, data={"billed": 1})
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(report.id)


def test_report_export_missing_type(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    url = reverse("report-export")

    response = internal_employee_client.get(url, data={"user": user.id})

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_report_detail(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create(user=user)

    url = reverse("report-detail", args=[report.id])
    response = internal_employee_client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "task_assignee__is_reviewer, task_assignee__is_manager, task_assignee__is_resource, is_external, expected",
    [
        (True, False, False, True, status.HTTP_400_BAD_REQUEST),
        (False, True, False, True, status.HTTP_400_BAD_REQUEST),
        (False, False, True, True, status.HTTP_201_CREATED),
        (True, False, False, False, status.HTTP_201_CREATED),
        (False, True, False, False, status.HTTP_201_CREATED),
        (False, False, True, False, status.HTTP_201_CREATED),
    ],
)
def test_report_create(
    auth_client, report_factory, task_factory, task_assignee, is_external, expected
):
    """Should create a new report and automatically set the user."""
    user = auth_client.user
    task = task_factory.create()
    task_assignee.user = user
    task_assignee.task = task
    task_assignee.save()

    if is_external:
        EmploymentFactory.create(user=user, is_external=True)
    else:
        EmploymentFactory.create(user=user, is_external=False)

    data = {
        "data": {
            "type": "reports",
            "id": None,
            "attributes": {
                "comment": "foo",
                "duration": "00:50:00",
                "date": "2017-02-01",
            },
            "relationships": {
                "task": {"data": {"type": "tasks", "id": task.id}},
                "verified-by": {"data": None},
            },
        }
    }

    url = reverse("report-list")

    response = auth_client.post(url, data)
    assert response.status_code == expected

    if response.status_code == status.HTTP_201_CREATED:
        json = response.json()
        assert json["data"]["relationships"]["user"]["data"]["id"] == str(user.id)

        assert json["data"]["relationships"]["task"]["data"]["id"] == str(task.id)


def test_report_create_billed(
    internal_employee_client, report_factory, project_factory, task_factory
):
    """Should create a new report and automatically set the user."""
    user = internal_employee_client.user
    project = project_factory.create(billed=True)
    task = task_factory.create(project=project)

    data = {
        "data": {
            "type": "reports",
            "id": None,
            "attributes": {
                "comment": "foo",
                "duration": "00:50:00",
                "date": "2017-02-01",
            },
            "relationships": {
                "task": {"data": {"type": "tasks", "id": task.id}},
                "verified-by": {"data": None},
            },
        }
    }

    url = reverse("report-list")

    response = internal_employee_client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED

    json = response.json()
    assert json["data"]["relationships"]["user"]["data"]["id"] == str(user.id)

    assert json["data"]["relationships"]["task"]["data"]["id"] == str(task.id)

    assert json["data"]["attributes"]["billed"]


def test_report_update_bulk(
    internal_employee_client,
    report_factory,
    task_factory,
):
    task = task_factory.create()
    report = report_factory.create(user=internal_employee_client.user)

    url = reverse("report-bulk")

    data = {
        "data": {
            "type": "report-bulks",
            "id": None,
            "relationships": {"task": {"data": {"type": "tasks", "id": task.id}}},
        }
    }

    response = internal_employee_client.post(url + "?editable=1", data)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    report.refresh_from_db()
    assert report.task == task


def test_report_update_bulk_verify_non_reviewer(
    internal_employee_client,
    report_factory,
):
    report_factory.create(user=internal_employee_client.user)

    url = reverse("report-bulk")

    data = {
        "data": {"type": "report-bulks", "id": None, "attributes": {"verified": True}}
    }

    response = internal_employee_client.post(url + "?editable=1", data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_report_update_bulk_verify_superuser(superadmin_client, report_factory):
    user = superadmin_client.user
    EmploymentFactory.create(user=user)
    report = report_factory.create(user=user)

    url = reverse("report-bulk")

    data = {
        "data": {"type": "report-bulks", "id": None, "attributes": {"verified": True}}
    }

    response = superadmin_client.post(url + "?editable=1", data)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    report.refresh_from_db()
    assert report.verified_by == user


def test_report_update_bulk_verify_reviewer(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create(user=user)
    report.task.project.reviewers.add(user)

    url = reverse("report-bulk")

    data = {
        "data": {
            "type": "report-bulks",
            "id": None,
            "attributes": {"verified": True, "comment": "some comment"},
        }
    }

    response = internal_employee_client.post(
        url + "?editable=1&reviewer={0}".format(user.id), data
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    report.refresh_from_db()
    assert report.verified_by == user
    assert report.comment == "some comment"


def test_report_update_bulk_reset_verify(superadmin_client, report_factory):
    user = superadmin_client.user
    EmploymentFactory.create(user=user)
    report = report_factory.create(verified_by=user)

    url = reverse("report-bulk")

    data = {
        "data": {"type": "report-bulks", "id": None, "attributes": {"verified": False}}
    }

    response = superadmin_client.post(url + "?editable=1", data)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    report.refresh_from_db()
    assert report.verified_by_id is None


def test_report_update_bulk_not_editable(
    internal_employee_client,
    report_factory,
):
    url = reverse("report-bulk")

    data = {
        "data": {
            "type": "report-bulks",
            "id": None,
            "attributes": {"not_billable": True},
        }
    }

    response = internal_employee_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_report_update_verified_as_non_staff_but_owner(
    internal_employee_client,
    report_factory,
):
    """Test that an owner (not staff) may not change a verified report."""
    user = internal_employee_client.user
    report = report_factory.create(
        user=user, verified_by=user, duration=timedelta(hours=2)
    )

    url = reverse("report-detail", args=[report.id])

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"duration": "01:00:00"},
        }
    }

    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_report_update_owner(internal_employee_client, report_factory, task_factory):
    """Should update an existing report."""
    user = internal_employee_client.user
    report = report_factory.create(user=user)
    task = task_factory.create()

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {
                "comment": "foobar",
                "duration": "01:00:00",
                "date": "2017-02-04",
            },
            "relationships": {"task": {"data": {"type": "tasks", "id": task.id}}},
        }
    }

    url = reverse("report-detail", args=[report.id])

    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert (
        json["data"]["attributes"]["comment"] == data["data"]["attributes"]["comment"]
    )
    assert (
        json["data"]["attributes"]["duration"] == data["data"]["attributes"]["duration"]
    )
    assert json["data"]["attributes"]["date"] == data["data"]["attributes"]["date"]
    assert json["data"]["relationships"]["task"]["data"]["id"] == str(
        data["data"]["relationships"]["task"]["data"]["id"]
    )


def test_report_update_date_reviewer(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create()
    report.task.project.reviewers.add(user)

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"date": "2017-02-04"},
        }
    }

    url = reverse("report-detail", args=[report.id])

    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_report_update_duration_reviewer(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create(duration=timedelta(hours=2))
    report.task.project.reviewers.add(user)

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"duration": "01:00:00"},
        }
    }

    url = reverse("report-detail", args=[report.id])

    res = internal_employee_client.patch(url, data)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_report_update_by_user(
    internal_employee_client,
    report_factory,
):
    """Updating of report belonging to different user is not allowed."""
    report = report_factory.create()
    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"comment": "foobar"},
        }
    }

    url = reverse("report-detail", args=[report.id])
    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_report_update_verified_and_review_reviewer(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create(duration=timedelta(hours=2))
    report.task.project.reviewers.add(user)

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"review": True},
            "relationships": {
                "verified-by": {"data": {"id": user.pk, "type": "users"}}
            },
        }
    }

    url = reverse("report-detail", args=[report.id])

    res = internal_employee_client.patch(url, data)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_report_set_verified_by_user(
    internal_employee_client,
    report_factory,
):
    """Test that normal user may not verify report."""
    user = internal_employee_client.user
    report = report_factory.create(user=user)
    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "relationships": {
                "verified-by": {"data": {"id": user.id, "type": "users"}}
            },
        }
    }

    url = reverse("report-detail", args=[report.id])
    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_report_update_reviewer(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create(user=user)
    report.task.project.reviewers.add(user)

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"comment": "foobar"},
            "relationships": {
                "verified-by": {"data": {"id": user.id, "type": "users"}}
            },
        }
    }

    url = reverse("report-detail", args=[report.id])

    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK


def test_report_update_supervisor(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create(user=user)
    report.user.supervisors.add(user)

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"comment": "foobar"},
        }
    }

    url = reverse("report-detail", args=[report.id])

    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK


def test_report_verify_other_user(superadmin_client, report_factory, user_factory):
    """Verify that superuser may not verify to other user."""
    EmploymentFactory.create(user=superadmin_client.user)
    user = user_factory.create()
    report = report_factory.create()

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "relationships": {
                "verified-by": {"data": {"id": user.id, "type": "users"}}
            },
        }
    }

    url = reverse("report-detail", args=[report.id])
    response = superadmin_client.patch(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_report_reset_verified_by_reviewer(
    internal_employee_client,
    report_factory,
):
    """Test that reviewer may not change verified report."""
    user = internal_employee_client.user
    report = report_factory.create(user=user, verified_by=user)
    report.task.project.reviewers.add(user)

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"comment": "foobar"},
            "relationships": {"verified-by": {"data": None}},
        }
    }

    url = reverse("report-detail", args=[report.id])
    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    report.refresh_from_db()
    report.verified_by = None


def test_report_reset_verified_and_billed_by_reviewer(
    internal_employee_client,
    report_factory,
):
    """Test that reviewer may not change verified and billed report."""
    user = internal_employee_client.user
    report = report_factory.create(user=user, verified_by=user)
    report.task.project.reviewers.add(user)
    # Billed is not set on create because the factory doesnt seem to work with that
    report.billed = True
    report.save()

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"comment": "foobar"},
            "relationships": {"verified-by": {"data": None}},
        }
    }

    url = reverse("report-detail", args=[report.id])
    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    "task_assignee__is_reviewer, task_assignee__is_manager, task_assignee__is_resource, is_external, verified, expected",
    [
        (True, False, False, False, True, status.HTTP_403_FORBIDDEN),
        (True, False, False, False, False, status.HTTP_204_NO_CONTENT),
        (False, True, False, False, False, status.HTTP_204_NO_CONTENT),
        (False, True, False, False, True, status.HTTP_403_FORBIDDEN),
        (False, False, True, False, False, status.HTTP_204_NO_CONTENT),
        (False, False, True, False, True, status.HTTP_403_FORBIDDEN),
        (True, False, False, True, False, status.HTTP_403_FORBIDDEN),
        (False, True, False, True, False, status.HTTP_403_FORBIDDEN),
        (False, False, True, True, False, status.HTTP_204_NO_CONTENT),
        (True, False, False, True, True, status.HTTP_403_FORBIDDEN),
        (False, True, False, True, True, status.HTTP_403_FORBIDDEN),
        (False, False, True, True, True, status.HTTP_403_FORBIDDEN),
    ],
)
def test_report_delete_own_report(
    auth_client, report_factory, task_assignee, is_external, verified, expected
):
    user = auth_client.user
    task_assignee.user = user
    task_assignee.save()
    report = report_factory.create(user=user, task=task_assignee.task)

    if verified:
        report.verified_by = UserFactory.create()
        report.save()

    if is_external:
        EmploymentFactory.create(user=user, is_external=True)
    else:
        EmploymentFactory.create(user=user, is_external=False)

    url = reverse("report-detail", args=[report.id])
    response = auth_client.delete(url)
    assert response.status_code == expected


@pytest.mark.parametrize(
    "task_assignee__is_reviewer, task_assignee__is_manager, task_assignee__is_resource, is_external, verified",
    [
        (True, False, False, False, True),
        (True, False, False, False, False),
        (False, True, False, False, False),
        (False, True, False, False, True),
        (False, False, True, False, False),
        (False, False, True, False, True),
        (True, False, False, True, False),
        (True, False, False, True, True),
        (False, True, False, True, False),
        (False, True, False, True, True),
        (False, False, True, True, False),
        (False, False, True, True, True),
    ],
)
def test_report_delete_not_report_owner(
    auth_client, report_factory, task_assignee, is_external, verified
):
    user = auth_client.user
    task_assignee.user = user
    task_assignee.save()

    user2 = UserFactory.create()
    report = report_factory.create(user=user2, task=task_assignee.task)

    if verified:
        report.verified_by = UserFactory.create()
        report.save()

    if is_external:
        EmploymentFactory.create(user=user, is_external=True)
    else:
        EmploymentFactory.create(user=user, is_external=False)

    url = reverse("report-detail", args=[report.id])
    response = auth_client.delete(url)
    # status code 404 is expected, when the user cannot see the specific report
    # otherwise the user shouldn't be allowed to delete it, therefore code 403
    assert response.status_code in [
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ]


def test_report_round_duration(db, report_factory):
    """Should round the duration of a report to 15 minutes."""
    report = report_factory.create()

    report.duration = timedelta(hours=1, minutes=7)
    report.save()

    assert duration_string(report.duration) == "01:00:00"

    report.duration = timedelta(hours=1, minutes=8)
    report.save()

    assert duration_string(report.duration) == "01:15:00"

    report.duration = timedelta(hours=1, minutes=53)
    report.save()

    assert duration_string(report.duration) == "02:00:00"


def test_report_list_no_result(admin_client):
    EmploymentFactory.create(user=admin_client.user)
    url = reverse("report-list")
    res = admin_client.get(url)

    assert res.status_code == status.HTTP_200_OK
    json = res.json()
    assert json["meta"]["total-time"] == "00:00:00"


def test_report_delete_superuser(superadmin_client, report_factory):
    """Test that superuser may not delete reports of other users."""
    EmploymentFactory.create(user=superadmin_client.user)
    report = report_factory.create()
    url = reverse("report-detail", args=[report.id])

    response = superadmin_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_report_list_filter_cost_center(
    internal_employee_client,
    report_factory,
    cost_center_factory,
    project_factory,
    task_factory,
):
    cost_center = cost_center_factory.create()
    # 1st valid case: report with task of given cost center
    # but different project cost center
    task = task_factory.create(cost_center=cost_center)
    report_task = report_factory.create(task=task)
    # 2nd valid case: report with project of given cost center
    project = project_factory.create(cost_center=cost_center)
    task = task_factory.create(cost_center=None, project=project)
    report_project = report_factory.create(task=task)
    # Invalid case: report without cost center
    project = project_factory.create(cost_center=None)
    task = task_factory.create(cost_center=None, project=project)
    report_factory.create(task=task)

    url = reverse("report-list")

    res = internal_employee_client.get(url, data={"cost_center": cost_center.id})
    assert res.status_code == status.HTTP_200_OK
    json = res.json()
    assert len(json["data"]) == 2
    ids = {int(entry["id"]) for entry in json["data"]}
    assert {report_task.id, report_project.id} == ids


@pytest.mark.parametrize("file_type", ["csv", "xlsx", "ods"])
@pytest.mark.parametrize(
    "project_cs_name,task_cs_name,project_bt_name",
    [("Project cost center", "Task cost center", "Some billing type")],
)
@pytest.mark.parametrize(
    "project_cs,task_cs,expected_cs_name",
    [
        (True, True, "Task cost center"),
        (True, False, "Project cost center"),
        (False, True, "Task cost center"),
        (False, False, ""),
    ],
)
@pytest.mark.parametrize(
    "project_bt,expected_bt_name", [(True, "Some billing type"), (False, "")]
)
def test_report_export(
    internal_employee_client,
    django_assert_num_queries,
    report,
    task,
    project,
    cost_center_factory,
    file_type,
    project_cs,
    task_cs,
    expected_cs_name,
    project_bt,
    expected_bt_name,
    project_cs_name,
    task_cs_name,
    project_bt_name,
):
    report.task.project.cost_center = cost_center_factory(name=project_cs_name)
    report.task.cost_center = cost_center_factory(name=task_cs_name)
    report.task.project.billing_type.name = project_bt_name
    report.task.project.billing_type.save()

    if not project_cs:
        project.cost_center = None
    if not task_cs:
        task.cost_center = None
    if not project_bt:
        project.billing_type = None
    project.save()
    task.save()

    url = reverse("report-export")

    with django_assert_num_queries(2):
        response = internal_employee_client.get(url, data={"file_type": file_type})

    assert response.status_code == status.HTTP_200_OK

    book = pyexcel.get_book(file_content=response.content, file_type=file_type)
    # bookdict is a dict of tuples(name, content)
    sheet = book.bookdict.popitem()[1]

    assert len(sheet) == 2
    assert sheet[1][-2:] == [expected_bt_name, expected_cs_name]


@pytest.mark.parametrize(
    "settings_count,given_count,expected_status",
    [
        (-1, 9, status.HTTP_200_OK),
        (0, 9, status.HTTP_200_OK),
        (10, 9, status.HTTP_200_OK),
        (9, 10, status.HTTP_400_BAD_REQUEST),
    ],
)
def test_report_export_max_count(
    internal_employee_client,
    django_assert_num_queries,
    report_factory,
    task,
    settings,
    settings_count,
    given_count,
    expected_status,
):
    settings.REPORTS_EXPORT_MAX_COUNT = settings_count
    report_factory.create_batch(given_count, task=task)

    url = reverse("report-export")

    response = internal_employee_client.get(url, data={"file_type": "csv"})

    assert response.status_code == expected_status


def test_report_update_bulk_verify_reviewer_multiple_notify(
    internal_employee_client,
    task,
    task_factory,
    project,
    report_factory,
    user_factory,
    mailoutbox,
):
    reviewer = internal_employee_client.user
    project.reviewers.add(reviewer)

    user1, user2, user3 = user_factory.create_batch(3)
    report1_1 = report_factory(user=user1, task=task)
    report1_2 = report_factory(user=user1, task=task)
    report2 = report_factory(user=user2, task=task)
    report3 = report_factory(user=user3, task=task)

    other_task = task_factory()

    url = reverse("report-bulk")

    data = {
        "data": {
            "type": "report-bulks",
            "id": None,
            "attributes": {"verified": True, "comment": "some comment"},
            "relationships": {"task": {"data": {"type": "tasks", "id": other_task.id}}},
        }
    }

    query_params = (
        "?editable=1"
        f"&reviewer={reviewer.id}"
        "&id=" + ",".join(str(r.id) for r in [report1_1, report1_2, report2, report3])
    )
    response = internal_employee_client.post(url + query_params, data)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    for report in [report1_1, report1_2, report2, report3]:
        report.refresh_from_db()
        assert report.verified_by == reviewer
        assert report.comment == "some comment"
        assert report.task == other_task

    # every user received one mail
    assert len(mailoutbox) == 3
    assert all(True for mail in mailoutbox if len(mail.to) == 1)
    assert set(mail.to[0] for mail in mailoutbox) == set(
        user.email for user in [user1, user2, user3]
    )


@pytest.mark.parametrize("own_report", [True, False])
@pytest.mark.parametrize(
    "has_attributes,different_attributes,verified,expected",
    [
        (True, True, True, True),
        (True, True, False, True),
        (True, False, True, False),
        (False, None, True, False),
        (False, None, False, False),
    ],
)
def test_report_update_reviewer_notify(
    internal_employee_client,
    user_factory,
    report_factory,
    task_factory,
    mailoutbox,
    own_report,
    has_attributes,
    different_attributes,
    verified,
    expected,
):
    reviewer = internal_employee_client.user
    user = user_factory()

    if own_report:
        report = report_factory(user=reviewer, review=True)
    else:
        report = report_factory(user=user, review=True)
    report.task.project.reviewers.set([reviewer, user])
    new_task = task_factory(project=report.task.project)
    task = report.task
    TaskAssigneeFactory.create(user=user, is_resource=True, task=task)
    TaskAssigneeFactory.create(user=reviewer, is_reviewer=True, task=task)

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {},
            "relationships": {},
        }
    }
    if has_attributes:
        if different_attributes:
            data["data"]["attributes"] = {"comment": "foobar", "review": False}
            data["data"]["relationships"]["task"] = {
                "data": {"id": new_task.id, "type": "tasks"}
            }
        else:
            data["data"]["attributes"] = {"comment": report.comment}

    if verified:
        data["data"]["attributes"]["verified"] = verified

    url = reverse("report-detail", args=[report.id])

    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK

    mail_count = 1 if not own_report and expected else 0
    assert len(mailoutbox) == mail_count

    if mail_count:
        mail = mailoutbox[0]
        assert len(mail.to) == 1
        assert mail.to[0] == user.email


def test_report_notify_rendering(
    internal_employee_client,
    user_factory,
    project,
    report_factory,
    task_factory,
    mailoutbox,
    snapshot,
):
    reviewer = internal_employee_client.user
    user = user_factory()
    project.reviewers.add(reviewer)
    task1, task2, task3 = task_factory.create_batch(3, project=project)

    report1 = report_factory(
        user=user, task=task1, comment="original comment", not_billable=False
    )
    report2 = report_factory(
        user=user, task=task2, comment="some other comment", not_billable=False
    )
    report3 = report_factory(user=user, task=task3, comment="foo", not_billable=False)
    report4 = report_factory(
        user=user, task=task1, comment=report2.comment, not_billable=True
    )

    data = {
        "data": {
            "type": "report-bulks",
            "id": None,
            "attributes": {"comment": report2.comment, "not-billable": False},
            "relationships": {
                "task": {"data": {"id": report1.task.id, "type": "tasks"}}
            },
        }
    }

    url = reverse("report-bulk")

    query_params = (
        "?editable=1"
        f"&reviewer={reviewer.id}"
        "&id=" + ",".join(str(r.id) for r in [report1, report2, report3, report4])
    )
    response = internal_employee_client.post(url + query_params, data)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert len(mailoutbox) == 1
    snapshot.assert_match(mailoutbox[0].body)


@pytest.mark.parametrize(
    "report__review,needs_review", [(True, False), (False, True), (True, True)]
)
def test_report_update_bulk_review_and_verified(
    superadmin_client, project, task, report, user_factory, needs_review
):
    EmploymentFactory.create(user=superadmin_client.user)
    data = {
        "data": {"type": "report-bulks", "id": None, "attributes": {"verified": True}}
    }

    if needs_review:
        data["data"]["attributes"]["review"] = True

    url = reverse("report-bulk")

    query_params = f"?id={report.id}"
    response = superadmin_client.post(url + query_params, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_report_update_bulk_bill_non_reviewer(
    internal_employee_client,
    report_factory,
):
    report_factory.create(user=internal_employee_client.user)

    url = reverse("report-bulk")

    data = {"data": {"type": "report-bulks", "id": None, "attributes": {"billed": 1}}}

    response = internal_employee_client.post(url + "?editable=1", data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_report_update_bulk_bill_reviewer(
    internal_employee_client,
    report_factory,
):
    user = internal_employee_client.user
    report = report_factory.create(user=user)
    report.task.project.reviewers.add(user)

    url = reverse("report-bulk")

    data = {
        "data": {
            "type": "report-bulks",
            "id": None,
            "attributes": {"billed": True},
        }
    }

    response = internal_employee_client.post(
        url + "?editable=1&reviewer={0}".format(user.id), data
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    report.refresh_from_db()
    assert report.billed


def test_report_update_billed_user(
    internal_employee_client,
    report_factory,
):
    report = report_factory.create()

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"billed": 1},
        }
    }

    url = reverse("report-detail", args=[report.id])

    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_report_set_billed_by_user(
    internal_employee_client,
    report_factory,
):
    """Test that normal user may not bill report."""
    user = internal_employee_client.user
    report = report_factory.create(user=user)
    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"billed": 1},
        }
    }

    url = reverse("report-detail", args=[report.id])
    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_report_update_billed(internal_employee_client, report_factory, task):
    user = internal_employee_client.user
    report = report_factory.create(user=user)
    report.task.project.billed = True
    report.task.project.save()

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "attributes": {"comment": "foobar"},
        }
    }

    url = reverse("report-detail", args=[report.id])
    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK

    report.refresh_from_db()
    assert report.billed

    data = {
        "data": {
            "type": "reports",
            "id": report.id,
            "relationships": {
                "project": {"data": {"type": "projects", "id": task.project.id}},
                "task": {"data": {"type": "tasks", "id": task.id}},
            },
        }
    }

    response = internal_employee_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK

    report.refresh_from_db()
    assert not report.billed


def test_report_update_bulk_billed(internal_employee_client, report_factory, task):
    user = internal_employee_client.user
    report = report_factory.create(user=user)
    report.task.project.reviewers.add(user)
    task.project.billed = True
    task.project.save()

    url = reverse("report-bulk")

    data = {
        "data": {
            "type": "report-bulks",
            "id": None,
            "relationships": {
                "project": {"data": {"type": "projects", "id": task.project.id}},
                "task": {"data": {"type": "tasks", "id": task.id}},
            },
        }
    }

    response = internal_employee_client.post(
        url + "?editable=1&reviewer={0}".format(user.id), data
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    report.refresh_from_db()
    assert report.billed


def test_report_list_external_employee(external_employee_client, report_factory):
    user = external_employee_client.user
    report = report_factory.create(user=user, duration=timedelta(hours=1))
    TaskAssigneeFactory.create(user=user, task=report.task, is_resource=True)
    report_factory.create_batch(4)
    url = reverse("report-list")

    response = external_employee_client.get(
        url,
        data={
            "date": report.date,
            "user": user.id,
            "task": report.task_id,
            "project": report.task.project_id,
            "customer": report.task.project.customer_id,
            "include": ("user,task,task.project,task.project.customer,verified_by"),
        },
    )

    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert len(json["data"]) == 1
    assert json["data"][0]["id"] == str(report.id)
    assert json["meta"]["total-time"] == "01:00:00"
