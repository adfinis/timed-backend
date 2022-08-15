from django.contrib.auth import get_user_model
from rest_framework_json_api import relations
from rest_framework_json_api.serializers import DurationField, IntegerField, Serializer

from timed.projects.models import Customer, Project, Task
from timed.serializers import TotalTimeRootMetaMixin


class YearStatisticSerializer(TotalTimeRootMetaMixin, Serializer):
    duration = DurationField()
    year = IntegerField()

    class Meta:
        resource_name = "year-statistics"


class MonthStatisticSerializer(TotalTimeRootMetaMixin, Serializer):
    duration = DurationField()
    year = IntegerField()
    month = IntegerField()

    class Meta:
        resource_name = "month-statistics"


class CustomerStatisticSerializer(TotalTimeRootMetaMixin, Serializer):
    duration = DurationField()
    customer = relations.ResourceRelatedField(
        source="project__customer", model=Customer, read_only=True
    )

    included_serializers = {"customer": "timed.projects.serializers.CustomerSerializer"}

    class Meta:
        resource_name = "customer-statistics"


class ProjectStatisticSerializer(TotalTimeRootMetaMixin, Serializer):
    duration = DurationField()
    project = relations.ResourceRelatedField(
        model=Project, read_only=True
    )

    included_serializers = {"project": "timed.projects.serializers.ProjectSerializer"}

    class Meta:
        resource_name = "project-statistics"


class TaskStatisticSerializer(TotalTimeRootMetaMixin, Serializer):
    duration = DurationField(read_only=True)
    project = relations.ResourceRelatedField(model=Project, read_only=True)

    included_serializers = {"project": "timed.projects.serializers.ProjectSerializer"}

    class Meta:
        resource_name = "task-statistics"


class UserStatisticSerializer(TotalTimeRootMetaMixin, Serializer):
    duration = DurationField(read_only=True)
    user = relations.ResourceRelatedField(model=get_user_model(), read_only=True)

    included_serializers = {"user": "timed.employment.serializers.UserSerializer"}

    class Meta:
        resource_name = "user-statistics"
