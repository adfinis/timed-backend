from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from io import BytesIO
from typing import TYPE_CHECKING
from zipfile import ZipFile

from django.conf import settings
from django.db.models import F, Q, QuerySet, Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from django.http import HttpResponse
from django.utils.http import content_disposition_header
from ezodf import Cell, opendoc
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from timed.mixins import AggregateQuerysetMixin
from timed.permissions import IsAuthenticated, IsInternal, IsSuperUser
from timed.projects.models import Customer, Project, Task
from timed.reports import serializers
from timed.tracking.filters import ReportFilterSet
from timed.tracking.models import Report
from timed.tracking.views import ReportViewSet

from . import filters

if TYPE_CHECKING:
    from typing import Iterable

    from ezodf.document import FlatXMLDocument, PackagedDocument

    from timed.employment.models import User


class YearStatisticViewSet(AggregateQuerysetMixin, ReadOnlyModelViewSet):
    """Year statistics calculates total reported time per year."""

    serializer_class = serializers.YearStatisticSerializer
    filterset_class = ReportFilterSet
    ordering_fields = (
        "year",
        "duration",
    )
    ordering = ("year",)
    permission_classes = (
        (
            # internal employees or super users may read all customer statistics
            (IsInternal | IsSuperUser) & IsAuthenticated
        ),
    )

    def get_queryset(self):
        queryset = Report.objects.all()
        queryset = queryset.annotate(year=ExtractYear("date")).values("year")
        queryset = queryset.annotate(duration=Sum("duration"))
        return queryset.annotate(pk=F("year"))


class MonthStatisticViewSet(AggregateQuerysetMixin, ReadOnlyModelViewSet):
    """Month statistics calculates total reported time per month."""

    serializer_class = serializers.MonthStatisticSerializer
    filterset_class = ReportFilterSet
    ordering_fields = (
        "year",
        "month",
        "duration",
    )
    ordering = (
        "year",
        "month",
    )
    permission_classes = (
        (
            # internal employees or super users may read all customer statistics
            (IsInternal | IsSuperUser) & IsAuthenticated
        ),
    )

    def get_queryset(self):
        queryset = Report.objects.all()
        queryset = queryset.annotate(
            year=ExtractYear("date"), month=ExtractMonth("date")
        )
        queryset = queryset.values("year", "month")
        queryset = queryset.annotate(duration=Sum("duration"))
        return queryset.annotate(pk=F("year") * 100 + F("month"))


class StatisticQueryset(QuerySet):
    def __init__(self, catch_prefixes, *args, base_qs=None, agg_filters=None, **kwargs):
        super().__init__(*args, **kwargs)
        if base_qs is None:
            base_qs = self.model.objects.all()
        self._base = base_qs
        self._agg_filters = agg_filters
        self._catch_prefixes = catch_prefixes

    def filter(self, /, **kwargs):
        my_filters = {
            k: v for k, v in kwargs.items() if not k.startswith(self._catch_prefixes)
        }

        agg_filters = {
            k: v for k, v in kwargs.items() if k.startswith(self._catch_prefixes)
        }

        new_qs = self
        if my_filters:
            new_qs = self.filter_base(**my_filters)
        if agg_filters:
            new_qs = new_qs.filter_aggregate(**agg_filters)

        return new_qs

    def filter_base(self, *args, **kwargs):
        return StatisticQueryset(
            model=self.model,
            base_qs=self._base.filter(*args, **kwargs),
            catch_prefixes=self._catch_prefixes,
            agg_filters=self._agg_filters,
        )

    def _clone(self):
        return StatisticQueryset(
            model=self.model,
            base_qs=self._base._clone(),  # noqa: SLF001
            catch_prefixes=self._catch_prefixes,
            agg_filters=self._agg_filters,
        )

    def __str__(self) -> str:
        return f"StatisticQueryset({self._base!s} | {self._agg_filters!s})"

    def __repr__(self) -> str:
        return f"StatisticQueryset({self._base!r} | {self._agg_filters!r})"

    def filter_aggregate(self, *args, **kwargs):
        filter_q = Q(*args, **kwargs)

        new_filters = self._agg_filters & filter_q if self._agg_filters else filter_q

        return StatisticQueryset(
            model=self.model,
            base_qs=self._base,
            catch_prefixes=self._catch_prefixes,
            agg_filters=new_filters,
        )


class CustomerStatisticViewSet(AggregateQuerysetMixin, ReadOnlyModelViewSet):
    """Customer statistics calculates total reported time per customer."""

    serializer_class = serializers.CustomerStatisticSerializer
    filterset_class = filters.CustomerStatisticFilterSet
    ordering_fields = (
        "name",
        "duration",
        "estimated_time",
        "remaining_effort",
    )

    ordering = ("name",)
    permission_classes = (
        (
            # internal employees or super users may read all customer statistics
            (IsInternal | IsSuperUser) & IsAuthenticated
        ),
    )

    def get_queryset(self):
        return StatisticQueryset(model=Customer, catch_prefixes="projects__")


class ProjectStatisticViewSet(AggregateQuerysetMixin, ReadOnlyModelViewSet):
    """Project statistics calculates total reported time per project."""

    serializer_class = serializers.ProjectStatisticSerializer
    filterset_class = filters.ProjectStatisticFilterSet
    ordering_fields = (
        "name",
        "duration",
        "estimated_time",
        "remaining_effort",
    )
    ordering = ("name",)
    permission_classes = (
        (
            # internal employees or super users may read all customer statistics
            (IsInternal | IsSuperUser) & IsAuthenticated
        ),
    )

    def get_queryset(self):
        return StatisticQueryset(model=Project, catch_prefixes="tasks__")


class TaskStatisticViewSet(AggregateQuerysetMixin, ReadOnlyModelViewSet):
    """Task statistics calculates total reported time per task."""

    serializer_class = serializers.TaskStatisticSerializer
    filterset_class = filters.TaskStatisticFilterSet
    ordering_fields = (
        "name",
        "duration",
        "estimated_time",
        "remaining_effort",
    )
    ordering = ("name",)
    permission_classes = (
        (
            # internal employees or super users may read all customer statistics
            (IsInternal | IsSuperUser) & IsAuthenticated
        ),
    )

    def get_queryset(self):
        return StatisticQueryset(model=Task, catch_prefixes="tasks__")


class UserStatisticViewSet(AggregateQuerysetMixin, ReadOnlyModelViewSet):
    """User calculates total reported time per user."""

    serializer_class = serializers.UserStatisticSerializer
    filterset_class = ReportFilterSet
    ordering_fields = (
        "user__username",
        "duration",
    )
    ordering = ("user__username",)
    permission_classes = (
        (
            # internal employees or super users may read all customer statistics
            (IsInternal | IsSuperUser) & IsAuthenticated
        ),
    )

    def get_queryset(self):
        queryset = Report.objects.all()
        queryset = queryset.values("user")
        queryset = queryset.annotate(duration=Sum("duration"))
        return queryset.annotate(pk=F("user"))


class WorkReportViewSet(GenericViewSet):
    """Build a ods work report of reports with given filters.

    It creates one work report per project. If given filters results
    in several projects work reports will be returned as zip.
    """

    filterset_class = ReportFilterSet
    ordering = ReportViewSet.ordering
    ordering_fields = ReportViewSet.ordering_fields

    def get_queryset(self):
        """Don't show any reports to customers."""
        user = self.request.user

        queryset = Report.objects.select_related(
            "user", "task", "task__project", "task__project__customer"
        ).prefetch_related(
            # need to prefetch verified_by as select_related joins nullable
            # foreign key verified_by with INNER JOIN instead of LEFT JOIN
            # which leads to an empty result.
            # This only happens as user and verified_by points to same table
            # and user is not nullable
            "verified_by"
        )

        if user.get_active_employment():
            return queryset
        return queryset.none()

    def _parse_query_params(self, queryset, request):
        """Parse query params by using filterset_class."""
        fltr = self.filterset_class(
            request.query_params, queryset=queryset, request=request
        )
        form = fltr.form
        form.is_valid()
        return form.cleaned_data

    def _clean_filename(self, name: str) -> str:
        """Clean name so it can be used in file paths.

        To accomplish this it will remove all special chars and
        replace spaces with underscores
        """
        escaped = re.sub(r"[^\w\s-]", "", name)
        return re.sub(r"\s+", "_", escaped)

    def _generate_workreport_name(self, from_date: date, project: Project) -> str:
        """Generate workreport name.

        Name is in format: YYMM-YYYYMMDD-$Customer-$Project.ods
        whereas YYMM is year and month of from_date and YYYYMMDD
        is date when work reports gets created.
        """
        return f"{from_date:%y%m}-{date.today():%Y%m%d}-{self._clean_filename(project.customer.name)}-{self._clean_filename(project.name)}.ods"

    def _create_workreport(  # noqa: PLR0913
        self,
        from_date: date,
        to_date: date,
        project: Project,
        reports: Iterable[Report],
        user: User,
    ) -> tuple[str, PackagedDocument | FlatXMLDocument]:
        """Create ods workreport.

        :rtype: tuple
        :return: tuple where as first value is name and second ezodf document
        """
        customer = project.customer
        verifiers = sorted(
            {
                report.verified_by.get_full_name()
                for report in reports
                if report.verified_by_id is not None
            }
        )

        tmpl = settings.WORK_REPORT_PATH
        doc: PackagedDocument | FlatXMLDocument = opendoc(tmpl)
        table = doc.sheets[0]
        tasks = defaultdict(int)
        date_style = table["C5"].style_name
        # in template cell D3 is empty but styled for float and borders
        float_style = table["D3"].style_name
        # in template cell D4 is empty but styled for text wrap and borders
        text_style = table["D4"].style_name
        # in template cell D8 is empty but styled for date with borders
        date_style_report = table["D8"].style_name

        # for simplicity insert reports in reverse order
        for report in reports:
            table.insert_rows(12, 1)
            table["A13"] = Cell(
                report.date, style_name=date_style_report, value_type="date"
            )
            table["B13"] = Cell(report.user.get_full_name(), style_name=text_style)
            hours = report.duration.total_seconds() / 60 / 60
            table["C13"] = Cell(hours, style_name=float_style)
            table["D13"] = Cell(report.comment, style_name=text_style)
            table["E13"] = Cell(report.task.name, style_name=text_style)
            if report.not_billable:
                table["F13"] = Cell("no", style_name=float_style)
            else:
                table["F13"] = Cell("yes", style_name=float_style)

            # when from and to date are None find lowest and biggest date
            from_date = min(report.date, from_date or date.max)
            to_date = max(report.date, to_date or date.min)

            tasks[report.task.name] += hours

        # header values
        table["C3"] = Cell(customer and customer.name)
        table["C4"] = Cell(project and project.name)
        table["C5"] = Cell(from_date, style_name=date_style, value_type="date")
        table["C6"] = Cell(to_date, style_name=date_style, value_type="date")
        table["C8"] = Cell(date.today(), style_name=date_style, value_type="date")
        table["C9"] = Cell(user.get_full_name())
        table["C10"] = Cell(", ".join(verifiers))

        # reset temporary styles (mainly because of borders)
        table["D3"].style_name = ""
        table["D4"].style_name = ""
        table["D8"].style_name = ""

        pos = 13 + len(reports)
        for task_name, task_total_hours in tasks.items():
            table.insert_rows(pos, 1)
            table.row_info(pos).style_name = table.row_info(pos - 1).style_name
            table[pos, 0] = Cell(task_name, style_name=table[pos - 1, 0].style_name)
            table[pos, 2] = Cell(
                task_total_hours, style_name=table[pos - 1, 2].style_name
            )

        # calculate location of total hours as insert rows moved it
        table[
            13 + len(reports) + len(tasks), 2
        ].formula = f"of:=SUM(C13:C{13 + len(reports) - 1!s})"

        # calculate location of total not billable hours as insert rows moved it
        table[
            13 + len(reports) + len(tasks) + 1, 2
        ].formula = 'of:=SUMIF(F13:F{0};"no";C13:C{0})'.format(
            str(13 + len(reports) - 1)
        )

        name = self._generate_workreport_name(from_date, project)
        return (name, doc)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if queryset.count() == 0:
            return Response(
                "No entries were selected. Make sure to clear unneeded filters.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # needed as we add items in reverse order to work report
        queryset = queryset.reverse()

        if (
            settings.WORK_REPORTS_EXPORT_MAX_COUNT > 0
            and queryset.count() > settings.WORK_REPORTS_EXPORT_MAX_COUNT
        ):
            return Response(
                f"Your request exceeds the maximum allowed entries ({settings.WORK_REPORTS_EXPORT_MAX_COUNT})",
                status=status.HTTP_400_BAD_REQUEST,
            )

        params = self._parse_query_params(queryset, request)

        from_date = params.get("from_date")
        to_date = params.get("to_date")

        reports_by_project = defaultdict(list)
        for report in queryset:
            reports_by_project[report.task.project].append(report)

        docs = [
            self._create_workreport(from_date, to_date, project, reports, request.user)
            for project, reports in reports_by_project.items()
        ]

        if len(docs) == 1:
            name, doc = docs[0]
            response = HttpResponse(
                doc.tobytes(),
                content_type="application/vnd.oasis.opendocument.spreadsheet",
            )
            response["Content-Disposition"] = content_disposition_header(
                as_attachment=True, filename=name
            )
            return response

        # zip multiple work reports
        buf = BytesIO()
        with ZipFile(buf, "w") as zf:
            for name, doc in docs:
                zf.writestr(name, doc.tobytes())
        response = HttpResponse(buf.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = content_disposition_header(
            as_attachment=True, filename=f"{date.today():%Y%m%d}-WorkReports.zip"
        )
        return response
