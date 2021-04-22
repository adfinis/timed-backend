"""Tests for the migrate_reviewers command."""
from django.core.management import call_command

from timed.employment.factories import UserFactory
from timed.projects.factories import ProjectFactory
from timed.projects.models import ProjectAssignee


def test_migrate_reviewers(db):
    # create reviewer for a project
    reviewer = UserFactory.create()
    project = ProjectFactory.create()
    project.reviewers.add(reviewer)

    call_command("migrate_reviewers")

    assert ProjectAssignee.objects.all().count() == 1
    assert ProjectAssignee.objects.last().is_reviewer is True
