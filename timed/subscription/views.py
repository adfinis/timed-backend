from rest_framework import (decorators, exceptions, mixins, permissions,
                            response, status, viewsets)

from timed.projects.filters import ProjectFilterSet
from timed.projects.models import Project

from . import filters, models, serializers


class SubscriptionProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Subscription specific project view.

    Subscription projects are not archived projects
    which have a billing type with packages.
    """

    serializer_class = serializers.SubscriptionProjectSerializer
    filter_class = ProjectFilterSet
    ordering_fields = (
        'name',
        'id'
    )

    def get_queryset(self):
        return Project.objects.filter(
            archived=False,
            customer_visible=True
        )


class PackageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.PackageSerializer
    filter_class = filters.PackageFilter

    def get_queryset(self):
        return models.Package.objects.select_related(
            'billing_type'
        )


class OrderViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.DestroyModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    serializer_class = serializers.OrderSerializer
    filter_class = filters.OrderFilter

    @decorators.detail_route(
        methods=['post'],
        permission_classes=[
            permissions.IsAuthenticated,
            permissions.IsAdminUser
        ]
    )
    def confirm(self, request, pk=None):
        """
        Confirm order.

        Only allowed by staff members
        """
        order = self.get_object()
        order.acknowledged = True
        order.confirmedby = request.user
        order.save()

        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        return models.Order.objects.select_related(
            'project'
        )

    def perform_destroy(self, instance):
        if instance.acknowledged:
            # acknowledge orders may not be deleted
            raise exceptions.PermissionDenied()

        instance.delete()
