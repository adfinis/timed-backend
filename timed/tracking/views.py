"""Viewsets for the tracking app."""

import django_excel
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.utils.translation import ugettext_lazy as _
from rest_condition import C
from rest_framework import exceptions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from timed.permissions import (
    IsAuthenticated,
    IsDeleteOnly,
    IsNotTransferred,
    IsOwner,
    IsReadOnly,
    IsReviewer,
    IsSuperUser,
    IsSupervisor,
    IsUnverified,
)
from timed.serializers import AggregateObject
from timed.tracking import filters, models, serializers


class ActivityViewSet(ModelViewSet):
    """Activity view set."""

    serializer_class = serializers.ActivitySerializer
    filterset_class = filters.ActivityFilterSet
    permission_classes = [
        # users may not change transferred activities
        C(IsAuthenticated) & C(IsNotTransferred)
        | C(IsAuthenticated) & C(IsReadOnly)
    ]

    def get_queryset(self):
        """Filter the queryset by the user of the request.

        :return: The filtered activities
        :rtype:  QuerySet
        """
        return models.Activity.objects.select_related(
            "task", "user", "task__project", "task__project__customer"
        ).filter(user=self.request.user)


class AttendanceViewSet(ModelViewSet):
    """Attendance view set."""

    serializer_class = serializers.AttendanceSerializer
    filterset_class = filters.AttendanceFilterSet

    def get_queryset(self):
        """Filter the queryset by the user of the request.

        :return: The filtered attendances
        :rtype:  QuerySet
        """
        return models.Attendance.objects.select_related("user").filter(
            user=self.request.user
        )


class ReportViewSet(ModelViewSet):
    """Report view set."""

    serializer_class = serializers.ReportSerializer
    filterset_class = filters.ReportFilterSet
    permission_classes = [
        # superuser may edit all reports but not delete
        C(IsSuperUser) & ~C(IsDeleteOnly)
        |
        # reviewer and supervisor may change unverified reports
        # but not delete them
        (C(IsReviewer) | C(IsSupervisor)) & C(IsUnverified) & ~C(IsDeleteOnly)
        |
        # owner may only change its own unverified reports
        C(IsAuthenticated) & C(IsOwner) & C(IsUnverified)
        |
        # all authenticated users may read all reports
        C(IsAuthenticated) & C(IsReadOnly)
    ]
    ordering = ("date", "id")
    ordering_fields = (
        "id",
        "date",
        "duration",
        "task__project__customer__name",
        "task__project__name",
        "task__name",
        "user__username",
        "comment",
        "verified_by__username",
        "review",
        "not_billable",
    )

    def _extract_cost_center(self, report):
        """
        Extract cost center from given report.

        Cost center of task is prioritized higher than of
        project.
        """
        name = ""

        if report.task.project.cost_center:
            name = report.task.project.cost_center.name

        if report.task.cost_center:
            name = report.task.project.name

        return name

    def _extract_billing_type(self, report):
        """Extract billing type from given report."""
        name = ""

        if report.task.project.billing_type:
            name = report.task.project.billing_type.name

        return name

    @action(
        detail=False,
        methods=["get"],
        serializer_class=serializers.ReportIntersectionSerializer,
    )
    def intersection(self, request):
        """
        Get intersection in reports of common report fields.

        Use case is for api caller to know what fields are the same
        in a list of reports. This will be mainly used for bulk update.

        This will always return a single resource.
        """
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)

        # filter params represent main indication of result
        # so it can be used as id
        params = self.request.query_params.copy()
        ignore_params = {"ordering", "page", "page_size", "include"}
        for param in ignore_params.intersection(params.keys()):
            del params[param]

        data = AggregateObject(queryset=queryset, pk=params.urlencode())
        serializer = self.get_serializer(data)
        return Response(data=serializer.data)

    @action(
        detail=False,
        methods=["post"],
        # all users are allowed to bulk update but only on filtered result
        permission_classes=[IsAuthenticated],
        serializer_class=serializers.ReportBulkSerializer,
    )
    def bulk(self, request):
        user = request.user
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fields = {
            key: value
            for key, value in serializer.validated_data.items()
            # value equal None means do not touch whereas verified
            # is handled separately
            if value is not None and key != "verified"
        }

        editable = request.query_params.get("editable")
        if not user.is_superuser and not editable:
            raise exceptions.ParseError(
                _("Editable filter needs to be set for bulk update")
            )

        verified = serializer.validated_data.get("verified")
        if verified is not None:
            # only reviewer or superuser may verify reports
            # this is enforced when reviewer filter is set to current user
            reviewer_id = request.query_params.get("reviewer")
            if not user.is_superuser and str(reviewer_id) != str(user.id):
                raise exceptions.ParseError(
                    _("Reviewer filter needs to be set to verifying user")
                )

            verified_by = verified and user or None
            fields["verified_by"] = verified_by

        if fields:
            queryset.update(**fields)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["get"], detail=False)
    def export(self, request):
        """Export filtered reports to given file format."""
        queryset = self.get_queryset().select_related(
            "task__project__billing_type",
            "task__cost_center",
            "task__project__cost_center",
        )
        queryset = self.filter_queryset(queryset)
        colnames = [
            "Date",
            "Duration",
            "Customer",
            "Project",
            "Task",
            "User",
            "Comment",
            "Billing Type",
            "Cost Center",
        ]
        content = [
            [
                report.date,
                report.duration,
                report.task.project.customer.name,
                report.task.project.name,
                report.task.name,
                report.user.username,
                report.comment,
                self._extract_billing_type(report),
                self._extract_cost_center(report),
            ]
            for report in queryset
        ]

        file_type = request.query_params.get("file_type")
        if file_type not in ["csv", "xlsx", "ods"]:
            return HttpResponseBadRequest()

        sheet = django_excel.pe.Sheet(content, name="Report", colnames=colnames)
        return django_excel.make_response(
            sheet, file_type=file_type, file_name="report.%s" % file_type
        )

    def get_queryset(self):
        """Select related to reduce queries.

        :return: The filtered reports
        :rtype:  QuerySet
        """
        return models.Report.objects.select_related("task", "user").select_related(
            "task__project", "task__project__customer"
        )


class AbsenceViewSet(ModelViewSet):
    """Absence view set."""

    serializer_class = serializers.AbsenceSerializer
    filterset_class = filters.AbsenceFilterSet

    permission_classes = [
        # superuser can change all but not delete
        C(IsAuthenticated) & C(IsSuperUser) & ~C(IsDeleteOnly)
        |
        # owner may change all its absences
        C(IsAuthenticated) & C(IsOwner)
        |
        # all authenticated users may read filtered result
        C(IsAuthenticated) & C(IsReadOnly)
    ]

    def get_queryset(self):
        user = self.request.user

        queryset = models.Absence.objects.select_related("type", "user")

        if not user.is_superuser:
            queryset = queryset.filter(Q(user=user) | Q(user__supervisors=user))

        return queryset
