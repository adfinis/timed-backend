"""Viewsets for the tracking app."""

from datetime import date

import django_excel
from django.conf import settings
from django.db.models import Case, CharField, F, Q, Value, When
from django.http import HttpResponseBadRequest
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from timed.employment.models import Employment
from timed.permissions import (
    IsAuthenticated,
    IsExternal,
    IsInternal,
    IsNotBilledAndVerfied,
    IsNotDelete,
    IsNotTransferred,
    IsOwner,
    IsReadOnly,
    IsResource,
    IsReviewer,
    IsSuperUser,
    IsSupervisor,
    IsUnverified,
)
from timed.projects.models import Task
from timed.serializers import AggregateObject
from timed.tracking import filters, models, serializers

from . import tasks


class ActivityViewSet(ModelViewSet):
    """Activity view set."""

    serializer_class = serializers.ActivitySerializer
    filterset_class = filters.ActivityFilterSet
    permission_classes = [
        # users may not change transferred activities
        IsAuthenticated & IsInternal & IsNotTransferred
        | IsAuthenticated & IsReadOnly
        # only external employees with resource role may create not transferred activities
        | IsAuthenticated & IsExternal & IsResource & IsNotTransferred
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
    permission_classes = [
        # superuser may edit all reports but not delete
        IsSuperUser & IsNotDelete
        # internal employees may change own attendances
        | IsAuthenticated & IsInternal
        # only external employees with resource role may change own attendances
        | IsAuthenticated & IsExternal & IsResource
    ]

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
    queryset = models.Report.objects.select_related(
        "task", "user", "task__project", "task__project__customer"
    )
    permission_classes = [
        # superuser may edit all reports but not delete
        IsSuperUser & IsNotDelete
        # reviewer and supervisor may change reports which are not verfied and billed
        # but not delete them
        | (IsReviewer | IsSupervisor) & IsNotBilledAndVerfied & IsNotDelete
        # internal employees may only change its own unverified reports
        # only external employees with resource role may only change its own unverified reports
        | IsOwner & IsUnverified & (IsInternal | (IsExternal & IsResource))
        # all authenticated users may read all reports
        | IsAuthenticated & IsReadOnly
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

    def get_queryset(self):
        """Get filtered reports for external employees."""
        user = self.request.user
        current_employment = Employment.objects.get_at(user=user, date=date.today())
        queryset = super().get_queryset()
        queryset.select_related(
            "task", "user", "task__project", "task__project__customer"
        )

        if not current_employment.is_external:
            return queryset

        assigned_tasks = Task.objects.filter(
            Q(task_assignees__user=user, task_assignees__is_reviewer=True)
            | Q(
                project__project_assignees__user=user,
                project__project_assignees__is_reviewer=True,
            )
            | Q(
                project__customer__customer_assignees__user=user,
                project__customer__customer_assignees__is_reviewer=True,
            )
        )
        queryset = queryset.filter(Q(task__in=assigned_tasks) | Q(user=user))
        return queryset

    def update(self, request, *args, **kwargs):
        """Override so we can issue emails on update."""

        partial = kwargs.get("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        fields = {
            key: value
            for key, value in serializer.validated_data.items()
            # value equal None means do not touch
            if value is not None
        }
        if fields and request.user != instance.user:
            tasks.notify_user_changed_report(instance, fields, request.user)

        return super().update(request, *args, **kwargs)

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

        verified = serializer.validated_data.pop("verified", None)
        fields = {
            key: value
            for key, value in serializer.validated_data.items()
            # value equal None means do not touch
            if value is not None
        }

        editable = request.query_params.get("editable")
        if not user.is_superuser and not editable:
            raise exceptions.ParseError(
                _("Editable filter needs to be set for bulk update")
            )

        if verified is not None:
            # only reviewer or superuser may verify reports
            # this is enforced when reviewer filter is set to current user
            reviewer_id = request.query_params.get("reviewer")
            if not user.is_superuser and str(reviewer_id) != str(user.id):
                raise exceptions.ParseError(
                    _("Reviewer filter needs to be set to verifying user")
                )

            fields["verified_by"] = verified and user or None

            if (
                "review" in fields
                and fields["review"]
                or any(queryset.values_list("review", flat=True))
            ):
                raise exceptions.ParseError(
                    _("Reports can't both be set as `review` and `verified`.")
                )

        if (
            serializer.validated_data.get("billed", None) is not None
            and not user.is_superuser
            and str(request.query_params.get("reviewer")) != str(user.id)
        ):
            raise exceptions.ParseError(
                _("Reviewer filter needs to be set to verifying user")
            )

        if "task" in fields:
            fields["billed"] = fields["task"].project.billed

        if fields:
            tasks.notify_user_changed_reports(queryset, fields, user)
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
        queryset = queryset.annotate(
            cost_center=Case(
                # Task cost center has precedence over project cost center
                When(
                    task__cost_center__isnull=False, then=F("task__cost_center__name")
                ),
                When(
                    task__project__cost_center__isnull=False,
                    then=F("task__project__cost_center__name"),
                ),
                default=Value(""),
                output_field=CharField(),
            )
        )
        queryset = queryset.annotate(
            billing_type=Case(
                When(
                    task__project__billing_type__isnull=False,
                    then=F("task__project__billing_type__name"),
                ),
                default=Value(""),
                output_field=CharField(),
            )
        )
        if (
            settings.REPORTS_EXPORT_MAX_COUNT > 0
            and queryset.count() > settings.REPORTS_EXPORT_MAX_COUNT
        ):
            return Response(
                _(
                    "Your request exceeds the maximum allowed entries ({0} > {1})".format(
                        queryset.count(), settings.REPORTS_EXPORT_MAX_COUNT
                    )
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

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

        content = queryset.values_list(
            "date",
            "duration",
            "task__project__customer__name",
            "task__project__name",
            "task__name",
            "user__username",
            "comment",
            "billing_type",
            "cost_center",
        )

        file_type = request.query_params.get("file_type")
        if file_type not in ["csv", "xlsx", "ods"]:
            return HttpResponseBadRequest()

        sheet = django_excel.pe.Sheet(content, name="Report", colnames=colnames)
        return django_excel.make_response(
            sheet, file_type=file_type, file_name="report.%s" % file_type
        )


class AbsenceViewSet(ModelViewSet):
    """Absence view set."""

    serializer_class = serializers.AbsenceSerializer
    filterset_class = filters.AbsenceFilterSet
    permission_classes = [
        # superuser can change all but not delete
        IsAuthenticated & IsSuperUser & IsNotDelete
        # owner may change all its absences
        | IsAuthenticated & IsOwner & IsInternal
        # all authenticated users may read filtered result
        | IsAuthenticated & IsReadOnly
    ]

    def get_queryset(self):
        """Get absences only for internal employees."""
        user = self.request.user
        if user.is_superuser:
            queryset = models.Absence.objects.select_related("type", "user")
            return queryset

        queryset = models.Absence.objects.select_related("type", "user").filter(
            Q(user=user) | Q(user__in=user.supervisees.all())
        )
        return queryset
