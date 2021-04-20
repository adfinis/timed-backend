from django.core.management.base import BaseCommand
from timed.projects.models import Project, ProjectAssignee
from timed.employment.models import User


class Command(BaseCommand):
    help = """Migrate all reviewers from the Reviewers through table
    to the new ProjectAssignee through table"""

    def handle(self, *args, **kwargs):
        projects = Project.objects.all()

        for project in projects:
            for reviewer in project.reviewers.all():
                project_assignee = ProjectAssignee(
                    user=reviewer, project=project, is_reviewer=True
                )
                project_assignee.save()
