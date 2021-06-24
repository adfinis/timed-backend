"""Factories for testing the projects app."""

from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from timed.projects import models


class CustomerFactory(DjangoModelFactory):
    """Customer factory."""

    name = Faker("company")
    email = Faker("company_email")
    website = Faker("url")
    comment = Faker("sentence")
    archived = False

    class Meta:
        """Meta informations for the customer factory."""

        model = models.Customer


class BillingTypeFactory(DjangoModelFactory):
    name = Faker("currency_name")
    reference = None

    class Meta:
        model = models.BillingType


class CostCenterFactory(DjangoModelFactory):
    name = Faker("job")
    reference = None

    class Meta:
        model = models.CostCenter


class ProjectFactory(DjangoModelFactory):
    """Project factory."""

    name = Faker("catch_phrase")
    estimated_time = Faker("time_delta")
    archived = False
    billed = False
    comment = Faker("sentence")
    customer = SubFactory("timed.projects.factories.CustomerFactory")
    cost_center = SubFactory("timed.projects.factories.CostCenterFactory")
    billing_type = SubFactory("timed.projects.factories.BillingTypeFactory")

    class Meta:
        """Meta informations for the project factory."""

        model = models.Project


class TaskFactory(DjangoModelFactory):
    """Task factory."""

    name = Faker("company_suffix")
    estimated_time = Faker("time_delta")
    archived = False
    project = SubFactory("timed.projects.factories.ProjectFactory")
    cost_center = SubFactory("timed.projects.factories.CostCenterFactory")

    class Meta:
        """Meta informations for the task factory."""

        model = models.Task


class TaskTemplateFactory(DjangoModelFactory):
    """Task template factory."""

    name = Faker("sentence")

    class Meta:
        """Meta informations for the task template factory."""

        model = models.TaskTemplate


class CustomerAssigneeFactory(DjangoModelFactory):
    """CustomerAssignee factory."""

    user = SubFactory("timed.employment.factories.UserFactory")
    customer = SubFactory("timed.projects.factories.CustomerFactory")
    is_resource = False
    is_reviewer = False
    is_manager = False

    class Meta:
        """Meta informations for the task template factory."""

        model = models.CustomerAssignee


class ProjectAssigneeFactory(DjangoModelFactory):
    """ProjectAssignee factory."""

    user = SubFactory("timed.employment.factories.UserFactory")
    project = SubFactory("timed.projects.factories.ProjectFactory")
    is_resource = False
    is_reviewer = False
    is_manager = False

    class Meta:
        """Meta informations for the task template factory."""

        model = models.ProjectAssignee


class TaskAssigneeFactory(DjangoModelFactory):
    """CustomerAssignee factory."""

    user = SubFactory("timed.employment.factories.UserFactory")
    task = SubFactory("timed.projects.factories.TaskFactory")
    is_resource = False
    is_reviewer = False
    is_manager = False

    class Meta:
        """Meta informations for the task template factory."""

        model = models.TaskAssignee
