"""Serializers for the projects app."""
from datetime import timedelta

from django.db.models import Q, Sum
from django.utils.duration import duration_string
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from timed.projects import models
from timed.tracking.models import Report


class CustomerSerializer(ModelSerializer):
    """Customer serializer."""

    included_serializers = {
        "assignees": "timed.employment.serializers.UserSerializer",
    }

    class Meta:
        """Meta information for the customer serializer."""

        model = models.Customer
        fields = [
            "name",
            "reference",
            "email",
            "website",
            "comment",
            "archived",
            "assignees",
        ]


class BillingTypeSerializer(ModelSerializer):
    class Meta:
        model = models.BillingType
        fields = ["name", "reference"]


class CostCenterSerializer(ModelSerializer):
    class Meta:
        model = models.CostCenter
        fields = ["name", "reference"]


class ProjectSerializer(ModelSerializer):
    """Project serializer."""

    customer = ResourceRelatedField(queryset=models.Customer.objects.all())
    billing_type = ResourceRelatedField(queryset=models.BillingType.objects.all())

    included_serializers = {
        "customer": "timed.projects.serializers.CustomerSerializer",
        "billing_type": "timed.projects.serializers.BillingTypeSerializer",
        "cost_center": "timed.projects.serializers.CostCenterSerializer",
        "reviewers": "timed.employment.serializers.UserSerializer",
        "assignees": "timed.employment.serializers.UserSerializer",
    }

    def get_root_meta(self, resource, many):
        if not many:
            queryset = Report.objects.filter(task__project=self.instance)
            data = queryset.aggregate(spent_time=Sum("duration"))
            data["spent_time"] = duration_string(data["spent_time"] or timedelta(0))

            billable_data = queryset.filter(not_billable=False, review=False).aggregate(
                spent_billable=Sum("duration")
            )
            data["spent_billable"] = duration_string(
                billable_data["spent_billable"] or timedelta(0)
            )
            return data

        return {}

    class Meta:
        """Meta information for the project serializer."""

        model = models.Project
        fields = [
            "name",
            "reference",
            "comment",
            "estimated_time",
            "archived",
            "billed",
            "customer",
            "billing_type",
            "cost_center",
            "reviewers",
            "customer_visible",
            "assignees",
        ]


class TaskSerializer(ModelSerializer):
    """Task serializer."""

    project = ResourceRelatedField(queryset=models.Project.objects.all())

    included_serializers = {
        "activities": "timed.tracking.serializers.ActivitySerializer",
        "project": "timed.projects.serializers.ProjectSerializer",
        "cost_center": "timed.projects.serializers.CostCenterSerializer",
        "assignees": "timed.employment.serializers.UserSerializer",
    }

    def get_root_meta(self, resource, many):
        if not many:
            queryset = Report.objects.filter(task=self.instance)
            data = queryset.aggregate(spent_time=Sum("duration"))
            data["spent_time"] = duration_string(data["spent_time"] or timedelta(0))
            return data

        return {}

    def validate(self, data):
        """Validate the role of the user.

        Check if the user is a manager on the corresponding
        project or customer when he wants to create a new task.

        Check if the user is a manager on the task or
        the corresponding project or customer when he wants to update the task.
        """
        request = self.context["request"]
        user = request.user
        if self.instance:
            if (
                models.Task.objects.filter(id=self.instance.id)
                .filter(
                    Q(
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
                )
                .exists()
            ):
                return data
        elif (
            models.Project.objects.filter(pk=data["project"].id)
            .filter(
                Q(
                    project_assignees__user=user,
                    project_assignees__is_manager=True,
                )
                | Q(
                    customer__customer_assignees__user=user,
                    customer__customer_assignees__is_manager=True,
                )
            )
            .exists()
        ):
            return data

    class Meta:
        """Meta information for the task serializer."""

        model = models.Task
        fields = [
            "name",
            "reference",
            "estimated_time",
            "archived",
            "project",
            "cost_center",
            "assignees",
        ]
