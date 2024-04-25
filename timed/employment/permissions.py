from rest_framework.permissions import BasePermission


class NoReports(BasePermission):
    def has_object_permission(self, _view, _request, obj):
        return not obj.reports.exists()
