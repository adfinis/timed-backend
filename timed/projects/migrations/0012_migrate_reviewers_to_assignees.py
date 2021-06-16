from django.db import migrations


def migrate_reviewers(apps, schema_editor):
    """Migrate reviewers from projects to assignees"""
    Project = apps.get_model("projects", "Project")
    ProjectAssignee = apps.get_model("projects", "ProjectAssignee")
    projects = Project.objects.all()

    for project in projects:
        for reviewer in project.reviewers.all():
            project_assignee = ProjectAssignee(
                user=reviewer, project=project, is_reviewer=True
            )
            project_assignee.save()


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0011_auto_20210419_1459"),
    ]

    operations = [
        migrations.RunPython(migrate_reviewers),
    ]
