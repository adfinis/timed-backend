from django.db.models import Sum
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from timed.tracking.models import Report


@receiver(pre_save, sender=Report)
def update_rejected_on_reports(sender, instance, **kwargs):
    """Unreject report when the task changes."""
    # Check if the report is being created or updated
    if instance.pk and instance.rejected:
        report = Report.objects.get(id=instance.id)
        if report.task_id != instance.task_id:
            instance.rejected = False


@receiver(post_save, sender=Report)
def update_most_recent_remaining_effort(sender, instance, **kwargs):
    """Update remaining effort on task, if remaining effort tracking is active."""
    if instance.task.project.remaining_effort_tracking:
        task = instance.task
        last_report = task.reports.order_by("date").last()
        if instance == last_report:
            task.most_recent_remaining_effort = instance.remaining_effort
            task.save()
        project = task.project
        total_remaining_effort = (
            project.tasks.all()
            .aggregate(sum_remaining=Sum("most_recent_remaining_effort"))
            .get("sum_remaining")
        )
        project.total_remaining_effort = total_remaining_effort
        project.save()
