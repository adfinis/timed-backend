from datetime import timedelta

from django.db.models import Sum
from django.utils.duration import duration_string


class TotalTimeRootMetaMixin(object):
    duration_field = "duration"

    def get_root_meta(self, resource, many):
        """Add total hours over whole result (not just page) to meta."""
        if many:
            view = self.context["view"]
            queryset = view.filter_queryset(view.get_queryset())
            data = queryset.aggregate(total_time=Sum(self.duration_field))
            data["total_time"] = duration_string(data["total_time"] or timedelta(0))
            return data
        return {}


class AggregateObject(dict):
    """
    Wrap dict into an object.

    All values will be accessible through attributes. Note that
    keys must be valid python names for this to work.
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super().__init__(**kwargs)
