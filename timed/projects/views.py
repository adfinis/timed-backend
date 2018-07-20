"""Viewsets for the projects app."""

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_json_api.views import PrefetchForIncludesHelperMixin

from timed.projects import filters, models, serializers


class CustomerViewSet(ReadOnlyModelViewSet):
    """Customer view set."""

    serializer_class = serializers.CustomerSerializer
    filterset_class     = filters.CustomerFilterSet
    ordering         = 'name'

    def get_queryset(self):
        """Prefetch related data.

        :return: The customers
        :rtype:  QuerySet
        """
        return models.Customer.objects.prefetch_related(
            'projects'
        )


class BillingTypeViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.BillingTypeSerializer
    ordering         = 'name'

    def get_queryset(self):
        return models.BillingType.objects.all()


class CostCenterViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.CostCenterSerializer
    ordering         = 'name'

    def get_queryset(self):
        return models.CostCenter.objects.all()


class ProjectViewSet(PrefetchForIncludesHelperMixin, ReadOnlyModelViewSet):
    """Project view set."""

    serializer_class = serializers.ProjectSerializer
    filterset_class     = filters.ProjectFilterSet
    ordering_fields  = ('customer__name', 'name',)
    ordering         = 'name'
    queryset         = models.Project.objects.all()

    prefetch_for_includes = {
        '__all__':   ['reviewers'],
        'reviewers': ['reviewers__supervisors'],
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related(
            'customer', 'billing_type', 'cost_center'
        )


class TaskViewSet(ReadOnlyModelViewSet):
    """Task view set."""

    serializer_class = serializers.TaskSerializer
    filterset_class     = filters.TaskFilterSet
    ordering         = 'name'

    def get_queryset(self):
        """Prefetch related data.

        :return: The tasks
        :rtype:  QuerySet
        """
        return models.Task.objects.select_related(
            'project', 'cost_center'
        )

    def filter_queryset(self, queryset):
        """Specific filter queryset options."""
        # my most frequent filter uses LIMIT so default ordering
        # needs to be disabled to avoid exception
        # see TODO filters.MyMostFrequentTaskFilter to avoid this
        if 'my_most_frequent' in self.request.query_params:
            self.ordering = None

        return super().filter_queryset(queryset)
