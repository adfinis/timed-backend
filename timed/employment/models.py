"""Models for the employment app."""

import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from timed.models import WeekdaysField


class EmploymentManager(models.Manager):
    """Custom manager for employments."""

    def for_user(self, user, date=datetime.date.today()):
        """Get the employment on a date for a user.

        :param User user: The user of the searched employment
        :param datetime.date date: The date of the searched employment
        :returns: The employment on the date for the user
        :rtype: timed.employment.models.Employment
        """
        return self.get(
            (
                models.Q(end_date__gte=date) |
                models.Q(end_date__isnull=True)
            ),
            start_date__lte=date,
            user=user
        )


class Location(models.Model):
    """Location model.

    A location is the place where an employee works.
    """

    name     = models.CharField(max_length=50, unique=True)
    workdays = WeekdaysField(default=[str(day) for day in range(1, 6)])
    """
    Workdays defined per location, default is Monday - Friday
    """

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return self.name


class UserManager(UserManager):
    def all_supervisors(self):
        objects = self.model.objects.annotate(
            supervisees_count=models.Count('supervisees'))
        return objects.filter(supervisees_count__gt=0)

    def all_supervisees(self):
        objects = self.model.objects.annotate(
            supervisors_count=models.Count('supervisors'))
        return objects.filter(supervisors_count__gt=0)


class User(AbstractUser):
    """Timed specific user."""

    supervisors = models.ManyToManyField('self', symmetrical=False,
                                         related_name='supervisees')
    objects = UserManager()


class Employment(models.Model):
    """Employment model.

    An employment represents a contract which defines where an employee works
    and from when to when.
    """

    user             = models.ForeignKey(settings.AUTH_USER_MODEL,
                                         related_name='employments')
    location         = models.ForeignKey(Location)
    percentage       = models.IntegerField(validators=[
                                           MinValueValidator(0),
                                           MaxValueValidator(100)])
    worktime_per_day = models.DurationField()
    start_date       = models.DateField()
    end_date         = models.DateField(blank=True, null=True)
    objects          = EmploymentManager()

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return '{0} ({1} - {2})'.format(
            self.user.username,
            self.start_date.strftime('%d.%m.%Y'),
            self.end_date.strftime('%d.%m.%Y') if self.end_date else 'today'
        )

    class Meta:
        """Meta information for the employment model."""

        indexes = [models.Index(fields=['start_date', 'end_date'])]


class PublicHoliday(models.Model):
    """Public holiday model.

    A public holiday is a day on which no employee of a certain location has
    to work.
    """

    name     = models.CharField(max_length=50)
    date     = models.DateField()
    location = models.ForeignKey(Location,
                                 related_name='public_holidays')

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return '{0} {1}'.format(self.name, self.date.strftime('%Y'))

    class Meta:
        """Meta information for the public holiday model."""

        indexes = [models.Index(fields=['date'])]


class AbsenceType(models.Model):
    """Absence type model.

    An absence type defines the type of an absence. E.g sickness, holiday or
    school.
    """

    name          = models.CharField(max_length=50)
    fill_worktime = models.BooleanField(default=False)

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return self.name


class AbsenceCredit(models.Model):
    """Absence credit model.

    An absence credit is a credit for an absence of a certain type. A user
    should only be able to create as many absences as defined in this credit.
    E.g a credit that defines that a user can only have 25 holidays.
    """

    user         = models.ForeignKey(settings.AUTH_USER_MODEL,
                                     related_name='absence_credits')
    absence_type = models.ForeignKey(AbsenceType)
    date         = models.DateField()
    duration     = models.DurationField(blank=True, null=True)


class OvertimeCredit(models.Model):
    """Overtime credit model.

    An overtime credit is a transferred overtime from the last year. This is
    added to the worktime of a user.
    """

    user     = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 related_name='overtime_credits')
    date     = models.DateField()
    duration = models.DurationField(blank=True, null=True)
