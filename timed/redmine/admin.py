from nested_inline.admin import NestedStackedInline

from timed.redmine.models import RedmineProject


class RedmineProjectInline(NestedStackedInline):
    model = RedmineProject
