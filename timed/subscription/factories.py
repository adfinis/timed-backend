from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from . import models


class OrderFactory(DjangoModelFactory):
    project = SubFactory("timed.projects.factories.ProjectFactory")
    duration = Faker("time_delta")

    class Meta:
        model = models.Order


class PackageFactory(DjangoModelFactory):
    billing_type = SubFactory("timed.projects.factories.BillingTypeFactory")
    duration = Faker("time_delta")
    price = Faker("pydecimal", positive=True, left_digits=4, right_digits=2)

    class Meta:
        model = models.Package
