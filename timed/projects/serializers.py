"""Serializers for the projects app."""
from datetime import timedelta

from django.db.models import Sum
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
