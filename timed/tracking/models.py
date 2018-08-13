"""Models for the tracking app."""

from datetime import timedelta

from django.conf import settings
from django.db import models


class Activity(models.Model):
    """Activity model.

    An activity represents a timeblock in which a user worked on a
    certain task.
    """

    from_time   = models.TimeField()
    to_time     = models.TimeField(blank=True, null=True)
    comment     = models.TextField(blank=True)
    date        = models.DateField()
    transferred = models.BooleanField(default=False)
    task        = models.ForeignKey('projects.Task',
                                    null=True,
                                    blank=True,
                                    related_name='activities')
    user        = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    related_name='activities')

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return '{0}: {1}'.format(self.user, self.task)

    class Meta:
        """Meta informations for the activity model."""

        verbose_name_plural = 'activities'
        indexes             = [models.Index(fields=['date'])]


class Attendance(models.Model):
    """Attendance model.

    An attendance is a timespan in which a user was present at work.
    Timespan should not be time zone aware hence splitting into date and
    from resp. to time fields.
    """

    date          = models.DateField()
    from_time     = models.TimeField()
    to_time       = models.TimeField()
    user          = models.ForeignKey(settings.AUTH_USER_MODEL,
                                      related_name='attendances')

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return '{0}: {1} {2} - {3}'.format(
            self.user,
            self.date.strftime('%Y-%m-%d'),
            self.from_time.strftime('%H:%M'),
            self.to_time.strftime('%H:%M')
        )


class Report(models.Model):
    """Report model.

    A report is a timespan in which a user worked on a certain task.
    The difference to the activity is, that this is going to be on the
    bill for the customer.
    """

    comment      = models.TextField(blank=True)
    date         = models.DateField()
    duration     = models.DurationField()
    review       = models.BooleanField(default=False)
    not_billable = models.BooleanField(default=False)
    task         = models.ForeignKey('projects.Task', related_name='reports')
    activity     = models.ForeignKey(Activity,
                                     null=True,
                                     blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='reports')
    user         = models.ForeignKey(settings.AUTH_USER_MODEL,
                                     related_name='reports')
    verified_by  = models.ForeignKey(settings.AUTH_USER_MODEL,
                                     on_delete=models.SET_NULL,
                                     null=True, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Save the report with some custom functionality.

        This rounds the duration of the report to the nearest 15 minutes.
        However, the duration must at least be 15 minutes long.
        """
        self.duration = timedelta(
            seconds=max(
                15 * 60,
                round(self.duration.seconds / (15 * 60)) * (15 * 60)
            )
        )

        super().save(*args, **kwargs)

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return '{0}: {1}'.format(self.user, self.task)

    class Meta:
        """Meta information for the report model."""

        indexes = [models.Index(fields=['date'])]


class AbsenceManager(models.Manager):
    def get_queryset(self):
        from timed.employment.models import PublicHoliday

        queryset = super().get_queryset()
        queryset = queryset.exclude(date__in=models.Subquery(
            PublicHoliday.objects.filter(
                location__employments__user=models.OuterRef('user')
            ).values('date')
        ))
        return queryset


class Absence(models.Model):
    """Absence model.

    An absence is time an employee was not working but still counts as
    worktime. E.g holidays or sickness.
    """

    comment  = models.TextField(blank=True)
    date     = models.DateField()
    type     = models.ForeignKey('employment.AbsenceType',
                                 related_name='absences')
    user     = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 related_name='absences')
    objects = AbsenceManager()

    def calculate_duration(self, employment):
        """
        Calculate duration of absence with given employment.

        For fullday absences duration is equal worktime per day of employment
        for absences which need to fill day calcuation needs to check
        how much time has been reported on that day.
        """
        if not self.type.fill_worktime:
            return employment.worktime_per_day

        reports = Report.objects.filter(date=self.date, user=self.user_id)
        data = reports.aggregate(reported_time=models.Sum('duration'))
        reported_time = data['reported_time'] or timedelta()
        if reported_time >= employment.worktime_per_day:
            # prevent negative duration in case user already
            # reported more time than worktime per day
            return timedelta()

        return employment.worktime_per_day - reported_time

    class Meta:
        """Meta informations for the absence model."""

        unique_together = ('date', 'user',)
