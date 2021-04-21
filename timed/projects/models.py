"""Models for the projects app."""

from django.conf import settings
from django.db import models
from djmoney.models.fields import MoneyField
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver


class Customer(models.Model):
    """Customer model.

    A customer is a person or company which will pay the work
    reported on their projects.
    """

    name = models.CharField(max_length=255, unique=True)
    reference = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    comment = models.TextField(blank=True)
    archived = models.BooleanField(default=False)
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="CustomerAssignee",
        related_name="assigned_to_customers",
    )

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return self.name

    class Meta:
        """Meta informations for the customer model."""

        ordering = ["name"]


class CostCenter(models.Model):
    """Cost center defining how cost of projects and tasks are allocated."""

    name = models.CharField(max_length=255, unique=True)
    reference = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class BillingType(models.Model):
    """Billing type defining how a project, resp. reports are being billed."""

    name = models.CharField(max_length=255, unique=True)
    reference = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Project(models.Model):
    """Project model.

    A project is an offer in most cases. It has multiple tasks and
    belongs to a customer.
    """

    name = models.CharField(max_length=255, db_index=True)
    reference = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    comment = models.TextField(blank=True)
    archived = models.BooleanField(default=False)
    billed = models.BooleanField(default=False)
    estimated_time = models.DurationField(blank=True, null=True)
    customer = models.ForeignKey(
        "projects.Customer", on_delete=models.CASCADE, related_name="projects"
    )
    billing_type = models.ForeignKey(
        BillingType,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="projects",
    )
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="projects",
    )
    reviewers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="reviews")
    customer_visible = models.BooleanField(default=False)
    amount_offered = MoneyField(
        max_digits=10, decimal_places=2, default_currency="CHF", blank=True, null=True
    )
    amount_invoiced = MoneyField(
        max_digits=10, decimal_places=2, default_currency="CHF", blank=True, null=True
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ProjectAssignee",
        related_name="assigned_to_projects",
    )

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return "{0} > {1}".format(self.customer, self.name)

    class Meta:
        ordering = ["name"]


class Task(models.Model):
    """Task model.

    A task is a certain activity type on a project. Users can
    report their activities and reports on it.
    """

    name = models.CharField(max_length=255)
    reference = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    estimated_time = models.DurationField(blank=True, null=True)
    archived = models.BooleanField(default=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="tasks"
    )
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="tasks",
    )
    amount_offered = MoneyField(
        max_digits=10, decimal_places=2, default_currency="CHF", blank=True, null=True
    )
    amount_invoiced = MoneyField(
        max_digits=10, decimal_places=2, default_currency="CHF", blank=True, null=True
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="TaskAssignee",
        related_name="assigned_to_tasks",
    )

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return "{0} > {1}".format(self.project, self.name)

    class Meta:
        """Meta informations for the task model."""

        ordering = ["name"]


class TaskTemplate(models.Model):
    """Task template model.

    A task template is a global template of a task which should
    be generated for every project.
    """

    name = models.CharField(max_length=255)

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return self.name

    class Meta:
        ordering = ["name"]


class CustomerAssignee(models.Model):
    """Customer assignee model.

    Customer assignee is an employee that is assigned to a specific customer.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_assignees",
    )
    customer = models.ForeignKey(
        "projects.Customer", on_delete=models.CASCADE, related_name="customer_assignees"
    )
    is_resource = models.BooleanField(default=False)
    is_reviewer = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)


class ProjectAssignee(models.Model):
    """Project assignee model.

    Project assignee is an employee that is assigned to a specific project.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_assignees",
    )
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="project_assignees"
    )
    is_resource = models.BooleanField(default=False)
    is_reviewer = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)


class TaskAssignee(models.Model):
    """Task assignee model.

    Task assignee is an employee that is assigned to a specific task.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_assignees",
    )
    task = models.ForeignKey(
        "projects.Task", on_delete=models.CASCADE, related_name="task_assignees"
    )
    is_resource = models.BooleanField(default=False)
    is_reviewer = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)


@receiver(post_save, sender=Project.assignees.through)
def create_or_update_project_assignee(sender, instance, created, **kwargs):
    """Create or update current project assignee and corresponding reviewer.

    If the created project assignee should be a reviewer, create a corresponding reviewer object.
    If a project assignee's is_reviewer attribute is updated, either create a new reviewer object or delete the corresponding one.
    """
    if instance.is_reviewer == True:
        if not Project.reviewers.through.objects.filter(
            user=instance.user, project=instance.project
        ):
            Project.reviewers.through.objects.create(
                user=instance.user, project=instance.project
            )
    elif not created and not instance.is_reviewer:
        Project.reviewers.through.objects.get(
            user=instance.user, project=instance.project
        ).delete()


@receiver(post_delete, sender=Project.assignees.through)
def delete_project_assignee(sender, instance, **kwargs):
    """Delete project assignee.

    If the project assignee is also a reviewer, delete the corresponding reviewer object.
    """
    if Project.reviewers.through.objects.filter(
        user=instance.user, project=instance.project
    ):
        Project.reviewers.through.objects.get(
            user=instance.user, project=instance.project
        ).delete()
