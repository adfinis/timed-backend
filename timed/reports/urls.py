from django.conf import settings
from rest_framework.routers import SimpleRouter

from . import views

r = SimpleRouter(trailing_slash=settings.APPEND_SLASH)

r.register(r"work-reports", views.WorkReportViewSet, "work-report")
r.register(r"year-statistics", views.YearStatisticViewSet, "year-statistic")
r.register(r"month-statistics", views.MonthStatisticViewSet, "month-statistic")
r.register(r"task-statistics", views.TaskStatisticViewSet, "task-statistic")
r.register(r"user-statistics", views.UserStatisticViewSet, "user-statistic")
r.register(r"customer-statistics", views.CustomerStatisticViewSet, "customer-statistic")
r.register(r"project-statistics", views.ProjectStatisticViewSet, "project-statistic")

urlpatterns = r.urls
