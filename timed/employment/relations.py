from django.contrib.auth import get_user_model
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import CurrentUserDefault


class CurrentUserResourceRelatedField(ResourceRelatedField):
    """User resource related field restricting user to current user."""

    def __init__(self, *args, **kwargs):
        kwargs["default"] = CurrentUserDefault()
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        request = self.context["request"]
        return get_user_model().objects.filter(pk=request.user.pk)
