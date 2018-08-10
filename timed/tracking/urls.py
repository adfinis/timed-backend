"""URL to view mapping for the tracking app."""

from django.conf import settings
from rest_framework.routers import SimpleRouter

from timed.tracking import views

r = SimpleRouter(trailing_slash=settings.APPEND_SLASH)

r.register(r'activities',      views.ActivityViewSet,      'activity')
r.register(r'attendances',     views.AttendanceViewSet,    'attendance')
r.register(r'reports',         views.ReportViewSet,        'report')
r.register(r'absences',        views.AbsenceViewSet,       'absence')

urlpatterns = r.urls
