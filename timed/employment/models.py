"""Models for the employment app."""

from datetime import date, timedelta

from dateutil import rrule
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum, functions
from django.utils.translation import gettext_lazy as _

from timed.models import WeekdaysField
from timed.tracking.models import Absence


class Location(models.Model):
    """Location model.

    A location is the place where an employee works.
    """

    name = models.CharField(max_length=50, unique=True)
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

    class Meta:
        ordering = ("name",)


class PublicHoliday(models.Model):
    """Public holiday model.

    A public holiday is a day on which no employee of a certain location has
    to work.
    """

    name = models.CharField(max_length=50)
    date = models.DateField()
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="public_holidays"
    )

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return "{0} {1}".format(self.name, self.date.strftime("%Y"))

    class Meta:
        """Meta information for the public holiday model."""

        indexes = [models.Index(fields=["date"])]
        ordering = ("date",)


class AbsenceType(models.Model):
    """Absence type model.

    An absence type defines the type of an absence. E.g sickness, holiday or
    school.
    """

    name = models.CharField(max_length=50)
    fill_worktime = models.BooleanField(default=False)

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return self.name

    def calculate_credit(self, user, start, end):
        """
        Calculate approved days of type for user in given time frame.

        For absence types which fill worktime this will be None.
        """
        if self.fill_worktime:
            return None

        credits = AbsenceCredit.objects.filter(
            user=user, absence_type=self, date__range=[start, end]
        )
        data = credits.aggregate(credit=Sum("days"))
        credit = data["credit"] or 0

        return credit

    def calculate_used_days(self, user, start, end):
        """
        Calculate used days of type for user in given time frame.

        For absence types which fill worktime this will be None.
        """
        if self.fill_worktime:
            return None

        absences = Absence.objects.filter(
            user=user, type=self, date__range=[start, end]
        )
        used_days = absences.count()
        return used_days

    class Meta:
        ordering = ("name",)


class AbsenceCredit(models.Model):
    """Absence credit model.

    An absence credit is a credit for an absence of a certain type. A user
    should only be able to create as many absences as defined in this credit.
    E.g a credit that defines that a user can only have 25 holidays.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="absence_credits",
    )
    comment = models.CharField(max_length=255, blank=True)
    absence_type = models.ForeignKey(AbsenceType, on_delete=models.PROTECT)
    date = models.DateField()
    days = models.IntegerField(default=0)
    transfer = models.BooleanField(default=False)
    """
    Mark whether this absence credit is a transfer from last year.
    """


class OvertimeCredit(models.Model):
    """Overtime credit model.

    An overtime credit is a transferred overtime from the last year. This is
    added to the worktime of a user.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="overtime_credits",
    )
    comment = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    duration = models.DurationField(default=timedelta(0))
    transfer = models.BooleanField(default=False)
    """
    Mark whether this absence credit is a transfer from last year.
    """


class EmploymentManager(models.Manager):
    """Custom manager for employments."""

    def get_at(self, user, date):
        """Get employment of user at given date.

        :param User user: The user of the searched employments
        :param datetime.date date: date of employment
        :returns: Employment
        """
        return self.get(
            (models.Q(end_date__gte=date) | models.Q(end_date__isnull=True)),
            start_date__lte=date,
            user=user,
        )

    def for_user(self, user, start, end):
        """Get employments in given time frame for current user.

        This includes overlapping employments.

        :param User user: The user of the searched employments
        :param datetime.date start: start of time frame
        :param datetime.date end: end of time frame
        :returns: queryset of employments
        """
        # end date NULL on database is like employment is ending today
        queryset = self.annotate(
            end=functions.Coalesce("end_date", models.Value(date.today()))
        )
        return queryset.filter(user=user).exclude(
            models.Q(end__lt=start) | models.Q(start_date__gt=end)
        )


class Employment(models.Model):
    """Employment model.

    An employment represents a contract which defines where an employee works
    and from when to when.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employments"
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name="employments"
    )
    percentage = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    worktime_per_day = models.DurationField()
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    objects = EmploymentManager()

    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_external = models.BooleanField(default=False)

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return "{0} ({1} - {2})".format(
            self.user.username,
            self.start_date.strftime("%d.%m.%Y"),
            self.end_date.strftime("%d.%m.%Y") if self.end_date else "today",
        )

    def calculate_worktime(self, start, end):
        """Calculate reported, expected and balance for employment.

        1. It shortens the time frame so it is within given employment
        1. Determine the count of workdays within time frame
        2. Determine the count of public holidays within time frame
        3. The expected worktime consists of following elements:
            * Workdays
            * Subtracted by holidays
            * Multiplied with the worktime per day of the employment
        4. Determine the overtime credit duration within time frame
        5. The reported worktime is the sum of the durations of all reports
           for this user within time frame
        6. The absences are all absences for this user within time frame
        7. The balance is the reported time plus the absences plus the
            overtime credit minus the expected worktime

        :param start: calculate worktime starting on given day.
        :param end:   calculate worktime till given day
        :returns:     tuple of 3 values reported, expected and delta in given
                      time frame
        """
        from timed.tracking.models import Absence, Report

        # shorten time frame to employment
        start = max(start, self.start_date)
        end = min(self.end_date or date.today(), end)

        # workdays is in isoweekday, byweekday expects Monday to be zero
        week_workdays = [int(day) - 1 for day in self.location.workdays]
        workdays = rrule.rrule(
            rrule.DAILY, dtstart=start, until=end, byweekday=week_workdays
        ).count()

        # converting workdays as db expects 1 (Sunday) to 7 (Saturday)
        workdays_db = [
            # special case for Sunday
            int(day) == 7 and 1 or int(day) + 1
            for day in self.location.workdays
        ]
        holidays = PublicHoliday.objects.filter(
            location=self.location,
            date__gte=start,
            date__lte=end,
            date__week_day__in=workdays_db,
        ).count()

        expected_worktime = self.worktime_per_day * (workdays - holidays)

        overtime_credit_data = OvertimeCredit.objects.filter(
            user=self.user_id, date__gte=start, date__lte=end
        ).aggregate(total_duration=Sum("duration"))
        overtime_credit = overtime_credit_data["total_duration"] or timedelta()

        reported_worktime_data = Report.objects.filter(
            user=self.user_id, date__gte=start, date__lte=end
        ).aggregate(duration_total=Sum("duration"))
        reported_worktime = reported_worktime_data["duration_total"] or timedelta()

        absences = sum(
            [
                absence.calculate_duration(self)
                for absence in Absence.objects.filter(
                    user=self.user_id, date__gte=start, date__lte=end
                ).select_related("type")
            ],
            timedelta(),
        )

        reported = reported_worktime + absences + overtime_credit

        return (reported, expected_worktime, reported - expected_worktime)

    class Meta:
        """Meta information for the employment model."""

        indexes = [models.Index(fields=["start_date", "end_date"])]


class UserManager(UserManager):
    def all_supervisors(self):
        objects = self.model.objects.annotate(
            supervisees_count=models.Count("supervisees")
        )
        return objects.filter(supervisees_count__gt=0)

    def all_reviewers(self):
        objects = self.model.objects.annotate(reviews_count=models.Count("reviews"))
        return objects.filter(reviews__gt=0)

    def all_supervisees(self):
        objects = self.model.objects.annotate(
            supervisors_count=models.Count("supervisors")
        )
        return objects.filter(supervisors_count__gt=0)


class User(AbstractUser):
    """Timed specific user."""

    supervisors = models.ManyToManyField(
        "self", symmetrical=False, related_name="supervisees"
    )

    tour_done = models.BooleanField(default=False)
    """
    Indicate whether user has finished tour through Timed in frontend.
    """

    last_name = models.CharField(_("last name"), max_length=30, blank=False)
    """
    Overwrite last name to make it required as interface relies on it.
    May also be name of organization if need to.
    """

    objects = UserManager()

    @property
    def is_reviewer(self):
        return self.reviews.exists()

    @property
    def user_id(self):
        """Map to id to be able to use generic permissions."""
        return self.id

    def calculate_worktime(self, start, end):
        """Calculate reported, expected and balance for user.

        This calculates summarizes worktime for all employments of users which
        are in given time frame.

        :param start: calculate worktime starting on given day.
        :param end:   calculate worktime till given day
        :returns:     tuple of 3 values reported, expected and delta in given
                      time frame
        """
        employments = Employment.objects.for_user(self, start, end).select_related(
            "location"
        )

        balances = [
            employment.calculate_worktime(start, end) for employment in employments
        ]

        reported = sum([balance[0] for balance in balances], timedelta())
        expected = sum([balance[1] for balance in balances], timedelta())
        balance = sum([balance[2] for balance in balances], timedelta())

        return (reported, expected, balance)
