from django.db.models import Sum
from django.db.models.signals import pre_save
from django.dispatch import receiver

from timed.tracking.models import Report


@receiver(pre_save, sender=Report)
def update_rejected_on_reports(sender, instance, **kwargs):  # noqa: ARG001
    """Unreject report when the task changes."""
    # Check if the report is being created or updated
    if instance.pk and instance.rejected:
        report = Report.objects.get(id=instance.id)
        if report.task_id != instance.task_id:
            instance.rejected = False


@receiver(pre_save, sender=Report)
def update_most_recent_remaining_effort(sender, instance, **kwargs):  # noqa: ARG001
    """Update remaining effort on task, if remaining effort tracking is active.

    Update most_recent_remaining_effort on task and total_remaining_effort on project
    only if remaining effort on report has changed.
    Any other change on report should not trigger this signal.
    """
    if kwargs.get("raw", False):  # pragma: no cover
        return

    if instance.task.project.remaining_effort_tracking is not True:
        return

    # update most_recent_remaining_effort and total_remaining_effort on report creation
    if not instance.pk:
        update_remaining_effort(instance)
        return

    # check if remaining effort has changed on report update
    if instance.remaining_effort != Report.objects.get(id=instance.id).remaining_effort:
        update_remaining_effort(instance)


def update_remaining_effort(report):
    task = report.task
    project = task.project

    task.most_recent_remaining_effort = report.remaining_effort
    task.save()

    total_remaining_effort = (
        task.project.tasks.all()
        .aggregate(sum_remaining=Sum("most_recent_remaining_effort"))
        .get("sum_remaining")
    )
    project.total_remaining_effort = total_remaining_effort
    project.save()
