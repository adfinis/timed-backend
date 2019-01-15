from datetime import timedelta

from django.db.models import Sum
from django.utils.duration import duration_string
from rest_framework_json_api.serializers import (
    CharField,
    ModelSerializer,
    SerializerMethodField,
)

from timed.projects.models import Project
from timed.tracking.models import Report

from .models import Order, Package


class SubscriptionProjectSerializer(ModelSerializer):
    purchased_time = SerializerMethodField(source="get_purchased_time")
    spent_time = SerializerMethodField(source="get_spent_time")

    def get_purchased_time(self, obj):
        """
        Calculate purchased time for given project.

        Only acknowledged hours are included.
        """
        orders = Order.objects.filter(project=obj, acknowledged=True)
        data = orders.aggregate(purchased_time=Sum("duration"))
        return duration_string(data["purchased_time"] or timedelta(0))

    def get_spent_time(self, obj):
        """
        Calculate spent time for given project.

        Reports which are not billable or are in review are excluded.
        """
        reports = Report.objects.filter(
            task__project=obj, not_billable=False, review=False
        )
        data = reports.aggregate(spent_time=Sum("duration"))
        return duration_string(data["spent_time"] or timedelta())

    included_serializers = {
        "billing_type": "timed.projects.serializers.BillingTypeSerializer",
        "customer": "timed.projects.serializers.CustomerSerializer",
        "orders": "timed.subscription.serializers.OrderSerializer",
    }

    class Meta:
        model = Project
        resource_name = "subscription-projects"
        fields = (
            "name",
            "billing_type",
            "purchased_time",
            "spent_time",
            "customer",
            "orders",
        )


class PackageSerializer(ModelSerializer):
    price = CharField()
    """CharField needed as it includes currency."""

    included_serializers = {
        "billing_type": "timed.projects.serializers.BillingTypeSerializer"
    }

    class Meta:
        model = Package
        resource_name = "subscription-packages"
        fields = ("duration", "price", "billing_type")


class OrderSerializer(ModelSerializer):

    included_serializers = {
        "project": ("timed.subscription.serializers" ".SubscriptionProjectSerializer")
    }

    class Meta:
        model = Order
        resource_name = "subscription-orders"
        fields = ("duration", "acknowledged", "ordered", "project")
