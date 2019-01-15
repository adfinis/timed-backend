"""Models for the projects app."""

from django.conf import settings
from django.db import models


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
    estimated_time = models.DurationField(blank=True, null=True)
    customer = models.ForeignKey(
        "projects.Customer", on_delete=models.CASCADE, related_name="projects"
    )
    billing_type = models.ForeignKey(
        BillingType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects",
    )
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects",
    )
    reviewers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="reviews")
    customer_visible = models.BooleanField(default=False)

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
