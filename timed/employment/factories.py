"""Factories for testing the tracking app."""

import datetime
import random

from django.contrib.auth import get_user_model
from factory import Faker, SubFactory, lazy_attribute
from factory.django import DjangoModelFactory

from timed.employment import models


class UserFactory(DjangoModelFactory):
    """User factory."""

    first_name = Faker("first_name")
    last_name = Faker("last_name")
    email = Faker("email")
    password = Faker("password", length=12)
    username = Faker("user_name")

    class Meta:
        """Meta informations for the user factory."""

        model = get_user_model()


class LocationFactory(DjangoModelFactory):
    """Location factory."""

    name = Faker("city")

    class Meta:
        """Meta informations for the location factory."""

        model = models.Location


class PublicHolidayFactory(DjangoModelFactory):
    """Public holiday factory."""

    name = Faker("word")
    date = Faker("date_object")
    location = SubFactory(LocationFactory)

    class Meta:
        """Meta informations for the public holiday factory."""

        model = models.PublicHoliday


class EmploymentFactory(DjangoModelFactory):
    """Employment factory."""

    user = SubFactory(UserFactory)
    location = SubFactory(LocationFactory)
    percentage = Faker("random_int", min=50, max=100)
    start_date = Faker("date_object")
    end_date = None

    @lazy_attribute
    def worktime_per_day(self):
        """Generate the worktime per day based on the percentage.

        :return: The generated worktime
        :rtype:  datetime.timedelta
        """
        return datetime.timedelta(minutes=60 * 8.5 * self.percentage / 100)

    class Meta:
        """Meta informations for the employment factory."""

        model = models.Employment


class AbsenceTypeFactory(DjangoModelFactory):
    """Absence type factory."""

    name = Faker("word")
    fill_worktime = False

    class Meta:
        """Meta informations for the absence type factory."""

        model = models.AbsenceType


class AbsenceCreditFactory(DjangoModelFactory):
    """Absence credit factory."""

    absence_type = SubFactory(AbsenceTypeFactory)
    user = SubFactory(UserFactory)
    date = Faker("date_object")
    days = Faker("random_int", min=1, max=25)

    class Meta:
        """Meta informations for the absence credit factory."""

        model = models.AbsenceCredit


class OvertimeCreditFactory(DjangoModelFactory):
    """Overtime credit factory."""

    user = SubFactory(UserFactory)
    date = Faker("date_object")

    @lazy_attribute
    def duration(self):
        """Generate a random duration.

        :return: The generated duration
        :rtype:  datetime.timedelta
        """
        return datetime.timedelta(hours=random.randint(5, 40))

    class Meta:
        """Meta informations for the overtime credit factory."""

        model = models.OvertimeCredit
