from django.db import models

from timed.projects.models import Project


class RedmineProject(models.Model):
    """
    Definition of a Redmine Project.

    Defines what Timed project belongs to what Redmine issue.
    """

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="redmine_project"
    )
    issue_id = models.PositiveIntegerField()
