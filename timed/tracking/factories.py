"""Factories for testing the tracking app."""

import datetime
from random import randint

from factory import Faker, SubFactory, lazy_attribute
from factory.django import DjangoModelFactory

from timed.tracking import models


class AttendanceFactory(DjangoModelFactory):
    """Attendance factory."""

    date = Faker("date")
    from_time = Faker("time")
    to_time = Faker("time")
    user = SubFactory("timed.employment.factories.UserFactory")

    class Meta:
        """Meta informations for the attendance factory."""

        model = models.Attendance


class ReportFactory(DjangoModelFactory):
    """Task factory."""

    comment = Faker("sentence")
    date = Faker("date")
    review = False
    not_billable = False
    task = SubFactory("timed.projects.factories.TaskFactory")
    user = SubFactory("timed.employment.factories.UserFactory")

    @lazy_attribute
    def duration(self):
        """Generate a random duration between 0 and 5 hours.

        :return: The generated duration
        :rtype:  datetime.timedelta
        """
        return datetime.timedelta(hours=randint(0, 4), minutes=randint(0, 59))

    class Meta:
        """Meta informations for the report factory."""

        model = models.Report


class ActivityFactory(DjangoModelFactory):
    """Activity factory."""

    comment = Faker("sentence")
    task = SubFactory("timed.projects.factories.TaskFactory")
    date = Faker("date")
    user = SubFactory("timed.employment.factories.UserFactory")
    from_time = Faker("time_object")
    transferred = False
    review = False
    not_billable = False

    @lazy_attribute
    def from_time(self):
        return datetime.time(hour=randint(0, 22), minute=randint(0, 59))

    @lazy_attribute
    def to_time(self):
        return self.from_time.replace(hour=self.from_time.hour + 1)

    class Meta:
        """Meta informations for the activity block factory."""

        model = models.Activity


class AbsenceFactory(DjangoModelFactory):
    """Absence factory."""

    user = SubFactory("timed.employment.factories.UserFactory")
    type = SubFactory("timed.employment.factories.AbsenceTypeFactory")
    date = Faker("date")

    class Meta:
        """Meta informations for the absence factory."""

        model = models.Absence
