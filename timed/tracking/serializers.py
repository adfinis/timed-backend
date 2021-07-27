"""Serializers for the tracking app."""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Case, Q, When
from django.utils.duration import duration_string
from django.utils.translation import gettext_lazy as _
from rest_framework_json_api import relations, serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import (
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    ValidationError,
)

from timed.employment.models import AbsenceType, Employment, PublicHoliday
from timed.employment.relations import CurrentUserResourceRelatedField
from timed.projects.models import Customer, Project, Task
from timed.serializers import TotalTimeRootMetaMixin
from timed.tracking import models


class ActivitySerializer(ModelSerializer):
    """Activity serializer."""

    user = CurrentUserResourceRelatedField()

    included_serializers = {
        "task": "timed.projects.serializers.TaskSerializer",
        "user": "timed.employment.serializers.UserSerializer",
    }

    def validate(self, data):
        """Validate the activity block.

        Ensure that a user can only have one activity
        which doesn't end before it started.
        """
        instance = self.instance
        from_time = data.get("from_time", instance and instance.from_time)
        to_time = data.get("to_time", instance and instance.to_time)
        user = instance and instance.user or data["user"]

        def validate_running_activity():
            if activity.filter(to_time__isnull=True).exists():
                raise ValidationError(_("A user can only have one active activity"))

        # validate that there is only one active activity
        activity = models.Activity.objects.filter(user=user)
        # if the request creates a new activity
        if instance is None and to_time is None:
            validate_running_activity()
        # if the request mutates an existsting activity
        if instance and instance.to_time and to_time is None:
            validate_running_activity()

        # validate that to is not before from
        if to_time is not None and to_time < from_time:
            raise ValidationError(_("An activity block may not end before it starts."))

        return data

    class Meta:
        """Meta information for the activity serializer."""

        model = models.Activity
        fields = "__all__"


class AttendanceSerializer(ModelSerializer):
    """Attendance serializer."""

    user = CurrentUserResourceRelatedField()

    included_serializers = {"user": "timed.employment.serializers.UserSerializer"}

    class Meta:
        """Meta information for the attendance serializer."""

        model = models.Attendance
        fields = ["date", "from_time", "to_time", "user"]


class ReportSerializer(TotalTimeRootMetaMixin, ModelSerializer):
    """Report serializer."""

    task = ResourceRelatedField(queryset=Task.objects.all())
    activity = ResourceRelatedField(
        queryset=models.Activity.objects.all(), allow_null=True, required=False
    )
    user = CurrentUserResourceRelatedField()
    verified_by = ResourceRelatedField(
        queryset=get_user_model().objects, required=False, allow_null=True
    )

    included_serializers = {
        "task": "timed.projects.serializers.TaskSerializer",
        "user": "timed.employment.serializers.UserSerializer",
        "verified_by": "timed.employment.serializers.UserSerializer",
    }

    def _validate_owner_only(self, value, field):
        if self.instance is not None:
            user = self.context["request"].user
            owner = self.instance.user
            if (
                getattr(self.instance, field) != value and user != owner
            ):  # rpragma: no cover
                raise ValidationError(_(f"Only owner may change {field}"))

        return value

    def validate_date(self, value):
        """Only owner is allowed to change date."""
        return self._validate_owner_only(value, "date")

    def validate_duration(self, value):
        """Only owner is allowed to change duration."""
        return self._validate_owner_only(value, "duration")

    def validate(self, data):
        """
        Validate that verified by is only set by reviewer or superuser.

        Additionally make sure a report is cannot be verified_by if is still
        needs review.

        External employees with manager or reviewer role may not create reports.
        """

        user = self.context["request"].user
        current_verified_by = self.instance and self.instance.verified_by
        new_verified_by = data.get("verified_by")
        task = data.get("task") or self.instance.task
        review = data.get("review")
        billed = data.get("billed")
        is_reviewer = (
            user.is_superuser or task.project.reviewers.filter(id=user.id).exists()
        )

        if new_verified_by != current_verified_by:
            if not is_reviewer:
                raise ValidationError(_("Only reviewer may verify reports."))

            if new_verified_by is not None and new_verified_by != user:
                raise ValidationError(_("You may only verifiy with your own user"))

            if new_verified_by and review:  # pragma: no cover
                raise ValidationError(
                    _("Report can't both be set as `review` and `verified`.")
                )

        if not is_reviewer and billed:
            raise ValidationError(_("Only reviewers may bill reports."))

        if not self.instance or billed is None:
            data["billed"] = task.project.billed

        current_employment = Employment.objects.get_at(user=user, date=date.today())

        if (
            self.context["request"].method == "POST"
            and current_employment.is_external
            and Task.objects.filter(
                Q(
                    task_assignees__user=user,
                    task_assignees__is_reviewer=True,
                )
                | Q(
                    project__project_assignees__user=user,
                    project__project_assignees__is_reviewer=True,
                )
                | Q(
                    project__customer__customer_assignees__user=user,
                    project__customer__customer_assignees__is_reviewer=True,
                )
                | Q(
                    task_assignees__user=user,
                    task_assignees__is_manager=True,
                )
                | Q(
                    project__project_assignees__user=user,
                    project__project_assignees__is_manager=True,
                )
                | Q(
                    project__customer__customer_assignees__user=user,
                    project__customer__customer_assignees__is_manager=True,
                )
            ).exists()
        ):
            raise ValidationError(
                "User is not a resource on the corresponding task, project or customer"
            )
        return data

    class Meta:
        model = models.Report
        fields = [
            "comment",
            "date",
            "duration",
            "review",
            "not_billable",
            "billed",
            "task",
            "activity",
            "user",
            "verified_by",
        ]


class ReportBulkSerializer(Serializer):
    """Serializer used for bulk updates of reports."""

    task = ResourceRelatedField(
        queryset=Task.objects.all(), allow_null=True, required=False
    )
    comment = serializers.CharField(allow_null=True, required=False)
    review = serializers.BooleanField(required=False, allow_null=True)
    not_billable = serializers.BooleanField(required=False, allow_null=True)
    billed = serializers.BooleanField(required=False, allow_null=True)
    verified = serializers.BooleanField(required=False, allow_null=True)

    class Meta:
        resource_name = "report-bulks"


class ReportIntersectionSerializer(Serializer):
    """
    Serializer of report intersections.

    Serializes a representation of all fields which are the same
    in given Report objects. If values of one field are not the same
    in all objects it will be represented as None.

    Serializer expect instance to have a queryset value.
    """

    customer = relations.SerializerMethodResourceRelatedField(
        source="get_customer", model=Customer, read_only=True
    )
    project = relations.SerializerMethodResourceRelatedField(
        source="get_project", model=Project, read_only=True
    )
    task = relations.SerializerMethodResourceRelatedField(
        source="get_task", model=Task, read_only=True
    )
    comment = SerializerMethodField()
    review = SerializerMethodField()
    not_billable = SerializerMethodField()
    billed = SerializerMethodField()
    verified = SerializerMethodField()

    def _intersection(self, instance, field, model=None):
        """Get intersection of given field.

        :return: Returns value of field if objects have same value;
                 otherwise None
        """
        value = None
        queryset = instance["queryset"]
        values = queryset.values(field).distinct()
        if values.count() == 1:
            value = values.first()[field]
            if model:
                value = model.objects.get(pk=value)

        return value

    def get_customer(self, instance):
        return self._intersection(instance, "task__project__customer", Customer)

    def get_project(self, instance):
        return self._intersection(instance, "task__project", Project)

    def get_task(self, instance):
        return self._intersection(instance, "task", Task)

    def get_comment(self, instance):
        return self._intersection(instance, "comment")

    def get_review(self, instance):
        return self._intersection(instance, "review")

    def get_not_billable(self, instance):
        return self._intersection(instance, "not_billable")

    def get_billed(self, instance):
        return self._intersection(instance, "billed")

    def get_verified(self, instance):
        queryset = instance["queryset"]
        queryset = queryset.annotate(
            verified=Case(
                When(verified_by_id__isnull=True, then=False),
                default=True,
                output_field=BooleanField(),
            )
        )
        instance["queryset"] = queryset
        return self._intersection(instance, "verified")

    def get_root_meta(self, resource, many):
        """Add number of results to meta."""
        queryset = self.instance["queryset"]
        return {"count": queryset.count()}

    included_serializers = {
        "customer": "timed.projects.serializers.CustomerSerializer",
        "project": "timed.projects.serializers.ProjectSerializer",
        "task": "timed.projects.serializers.TaskSerializer",
    }

    class Meta:
        resource_name = "report-intersections"


class AbsenceSerializer(ModelSerializer):
    """Absence serializer."""

    duration = SerializerMethodField(source="get_duration")
    type = ResourceRelatedField(queryset=AbsenceType.objects.all())
    user = CurrentUserResourceRelatedField()

    included_serializers = {
        "user": "timed.employment.serializers.UserSerializer",
        "type": "timed.employment.serializers.AbsenceTypeSerializer",
    }

    def get_duration(self, instance):
        try:
            employment = Employment.objects.get_at(instance.user, instance.date)
        except Employment.DoesNotExist:
            # absence is invalid if no employment exists on absence date
            return duration_string(timedelta())

        return duration_string(instance.calculate_duration(employment))

    def validate_date(self, value):
        """Only owner is allowed to change date."""
        if self.instance is not None:
            user = self.context["request"].user
            owner = self.instance.user
            if self.instance.date != value and user != owner:
                raise ValidationError(_("Only owner may change date"))

        return value

    def validate_type(self, value):
        """Only owner is allowed to change type."""
        if self.instance is not None:
            user = self.context["request"].user
            owner = self.instance.user
            if self.instance.date != value and user != owner:
                raise ValidationError(_("Only owner may change absence type"))

        return value

    def validate(self, data):
        """Validate the absence data.

        An absence should not be created on a public holiday or a weekend.

        :returns: The validated data
        :rtype:   dict
        """
        instance = self.instance
        user = data.get("user", instance and instance.user)
        try:
            location = Employment.objects.get_at(user, data.get("date")).location
        except Employment.DoesNotExist:  # pragma: no cover
            raise ValidationError(
                _("You can't create an absence on an unemployed day.")
            )

        if PublicHoliday.objects.filter(
            location_id=location.id, date=data.get("date")
        ).exists():
            raise ValidationError(_("You can't create an absence on a public holiday"))

        workdays = [int(day) for day in location.workdays]
        if data.get("date").isoweekday() not in workdays:
            raise ValidationError(_("You can't create an absence on a weekend"))

        return data

    class Meta:
        """Meta information for the absence serializer."""

        model = models.Absence
        fields = ["comment", "date", "duration", "type", "user"]
