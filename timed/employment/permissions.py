from rest_framework.permissions import BasePermission


class NoReports(BasePermission):
    def has_object_permission(self, _, __, obj):
        return not obj.reports.exists()
