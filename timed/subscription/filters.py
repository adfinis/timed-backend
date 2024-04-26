from __future__ import annotations

from typing import TYPE_CHECKING

from django_filters import FilterSet, NumberFilter

from timed.projects.models import Project

from . import models

if TYPE_CHECKING:
    from django.db.models import QuerySet


class PackageFilter(FilterSet):
    customer = NumberFilter(method="filter_customer")

    def filter_customer(
        self, queryset: QuerySet[models.Package], _name: str, value: int
    ) -> QuerySet[models.Package]:
        billing_types = Project.objects.filter(customer=value).values("billing_type")
        return queryset.filter(billing_type__in=billing_types)

    class Meta:
        model = models.Package
        fields = (
            "billing_type",
            "customer",
        )


class OrderFilter(FilterSet):
    customer = NumberFilter(field_name="project__customer")
    acknowledged = NumberFilter(field_name="acknowledged")

    class Meta:
        model = models.Order
        fields = (
            "customer",
            "project",
            "acknowledged",
        )
