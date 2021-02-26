"""Serializers for the employment app."""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Max, Value
from django.db.models.functions import Coalesce
from django.utils.duration import duration_string
from django.utils.translation import gettext_lazy as _
from rest_framework_json_api import relations
from rest_framework_json_api.serializers import (
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    ValidationError,
)

from timed.employment import models
from timed.tracking.models import Absence, Report


class UserSerializer(ModelSerializer):

    included_serializers = {
        "supervisors": "timed.employment.serializers.UserSerializer",
        "supervisees": "timed.employment.serializers.UserSerializer",
    }

    class Meta:
        """Meta information for the user serializer."""

        model = get_user_model()
        fields = [
            "email",
            "first_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "last_name",
            "supervisees",
            "supervisors",
            "tour_done",
            "username",
            "is_reviewer",
        ]
        read_only_fields = [
            "first_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "last_name",
            "supervisees",
            "supervisors",
            "username",
            "is_reviewer",
        ]


class WorktimeBalanceSerializer(Serializer):
    date = SerializerMethodField()
    balance = SerializerMethodField()
    user = relations.ResourceRelatedField(
        model=get_user_model(), read_only=True, source="id"
    )

    def get_date(self, instance):
        user = instance.id
        today = date.today()

        if instance.date is not None:
            return instance.date

        # calculate last reported day if no specific date is set
        max_absence_date = Absence.objects.filter(user=user, date__lt=today).aggregate(
            date=Max("date")
        )
        max_report_date = Report.objects.filter(user=user, date__lt=today).aggregate(
            date=Max("date")
        )

        last_reported_date = max(
            max_absence_date["date"] or date.min, max_report_date["date"] or date.min
        )

        instance.date = last_reported_date
        return instance.date

    def get_balance(self, instance):
        balance_date = self.get_date(instance)
        start = date(balance_date.year, 1, 1)

        # id is mapped to user instance
        _, _, balance = instance.id.calculate_worktime(start, balance_date)
        return duration_string(balance)

    included_serializers = {"user": "timed.employment.serializers.UserSerializer"}

    class Meta:
        resource_name = "worktime-balances"


class AbsenceBalanceSerializer(Serializer):
    credit = SerializerMethodField()
    used_days = SerializerMethodField()
    used_duration = SerializerMethodField()
    balance = SerializerMethodField()

    user = relations.ResourceRelatedField(model=get_user_model(), read_only=True)

    absence_type = relations.ResourceRelatedField(
        model=models.AbsenceType, read_only=True, source="id"
    )

    absence_credits = relations.SerializerMethodResourceRelatedField(
        source="get_absence_credits",
        model=models.AbsenceCredit,
        many=True,
        read_only=True,
    )

    def _get_start(self, instance):
        return date(instance.date.year, 1, 1)

    def get_credit(self, instance):
        """
        Calculate how many days are approved for given absence type.

        For absence types which fill worktime this will be None.
        """
        if "credit" in instance:
            return instance["credit"]

        # id is mapped to absence type
        absence_type = instance.id

        start = self._get_start(instance)

        # avoid multiple calculations as get_balance needs it as well
        instance["credit"] = absence_type.calculate_credit(
            instance.user, start, instance.date
        )
        return instance["credit"]

    def get_used_days(self, instance):
        """
        Calculate how many days are used of given absence type.

        For absence types which fill worktime this will be None.
        """
        if "used_days" in instance:
            return instance["used_days"]

        # id is mapped to absence type
        absence_type = instance.id

        start = self._get_start(instance)

        # avoid multiple calculations as get_balance needs it as well
        instance["used_days"] = absence_type.calculate_used_days(
            instance.user, start, instance.date
        )
        return instance["used_days"]

    def get_used_duration(self, instance):
        """
        Calculate duration of absence type.

        For absence types which fill worktime this will be None.
        """
        # id is mapped to absence type
        absence_type = instance.id
        if not absence_type.fill_worktime:
            return None

        start = self._get_start(instance)
        absences = sum(
            [
                absence.calculate_duration(
                    models.Employment.objects.get_at(instance.user, absence.date)
                )
                for absence in Absence.objects.filter(
                    user=instance.user,
                    date__range=[start, instance.date],
                    type_id=instance.id,
                ).select_related("type")
            ],
            timedelta(),
        )
        return duration_string(absences)

    def get_absence_credits(self, instance):
        """Get the absence credits for the user and type."""
        if "absence_credits" in instance:
            return instance["absence_credits"]

        # id is mapped to absence type
        absence_type = instance.id

        start = self._get_start(instance)
        absence_credits = models.AbsenceCredit.objects.filter(
            absence_type=absence_type,
            user=instance.user,
            date__range=[start, instance.date],
        ).select_related("user")

        # avoid multiple calculations when absence credits need to be included
        instance["absence_credits"] = absence_credits

        return absence_credits

    def get_balance(self, instance):
        # id is mapped to absence type
        absence_type = instance.id
        if absence_type.fill_worktime:
            return None

        return self.get_credit(instance) - self.get_used_days(instance)

    included_serializers = {
        "absence_type": "timed.employment.serializers.AbsenceTypeSerializer",
        "absence_credits": "timed.employment.serializers.AbsenceCreditSerializer",
    }

    class Meta:
        resource_name = "absence-balances"


class EmploymentSerializer(ModelSerializer):
    included_serializers = {
        "user": "timed.employment.serializers.UserSerializer",
        "location": "timed.employment.serializers.LocationSerializer",
    }

    def validate(self, data):
        """Validate the employment as a whole.

        Ensure the end date is after the start date and there is only one
        active employment per user and there are no overlapping employments.

        :throws: django.core.exceptions.ValidationError
        :return: validated data
        :rtype:  dict
        """
        instance = self.instance
        start_date = data.get("start_date", instance and instance.start_date)
        end_date = data.get("end_date", instance and instance.end_date)
        if end_date and start_date >= end_date:
            raise ValidationError(_("The end date must be after the start date"))

        user = data.get("user", instance and instance.user)
        employments = models.Employment.objects.filter(user=user)
        # end date not set means employment is ending today
        end_date = end_date or date.today()
        employments = employments.annotate(
            end=Coalesce("end_date", Value(date.today()))
        )
        if instance:
            employments = employments.exclude(id=instance.id)

        if any([e.start_date <= end_date and start_date <= e.end for e in employments]):
            raise ValidationError(
                _("A user can't have multiple employments at the same time")
            )

        return data

    class Meta:
        model = models.Employment
        fields = [
            "user",
            "location",
            "percentage",
            "worktime_per_day",
            "start_date",
            "end_date",
        ]


class LocationSerializer(ModelSerializer):
    """Location serializer."""

    class Meta:
        """Meta information for the location serializer."""

        model = models.Location
        fields = ["name", "workdays"]


class PublicHolidaySerializer(ModelSerializer):
    """Public holiday serializer."""

    location = relations.ResourceRelatedField(read_only=True)

    included_serializers = {
        "location": "timed.employment.serializers.LocationSerializer"
    }

    class Meta:
        """Meta information for the public holiday serializer."""

        model = models.PublicHoliday
        fields = ["name", "date", "location"]


class AbsenceTypeSerializer(ModelSerializer):
    """Absence type serializer."""

    class Meta:
        """Meta information for the absence type serializer."""

        model = models.AbsenceType
        fields = ["name", "fill_worktime"]


class AbsenceCreditSerializer(ModelSerializer):
    """Absence credit serializer."""

    included_serializers = {
        "absence_type": "timed.employment.serializers.AbsenceTypeSerializer"
    }

    class Meta:
        """Meta information for the absence credit serializer."""

        model = models.AbsenceCredit
        fields = ["user", "absence_type", "date", "days", "comment", "transfer"]


class OvertimeCreditSerializer(ModelSerializer):
    class Meta:
        model = models.OvertimeCredit
        fields = ["user", "date", "duration", "comment", "transfer"]
