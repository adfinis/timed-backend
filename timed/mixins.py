from rest_framework_json_api import relations

from timed.serializers import AggregateObject


class AggregateQuerysetMixin(object):
    """
    Add support for aggregate queryset in view.

    Wrap queryst dicts into aggregate object to support renderer
    which expect attributes.
    It additionally prefetches related instances represented as id in
    aggregate.

    In aggregates only an id of a related field is part of the object.
    Instead of loading each single object row by row this mixin prefetches
    all resource related fields and injects it before serialization starts.

    Mixin expects the id to be the same key as the resource related
    field defined in the serializer.

    To reduce number of queries `prefetch_related_for_field` can be defined
    to prefetch related data per field like the following:
    >>> from rest_framework.viewsets import ReadOnlyModelViewSet
    ... class MyView(ReadOnlyModelViewSet, AggregateQuerysetMixin):
    ...   # ...
    ...   prefetch_related_for_field = {
    ...     'field_name': ['field_name_prefetch']
    ...   }
    ...   # ...
    """

    def _is_related_field(self, val):
        """
        Check whether value is a related field.

        Ignores serializer method fields which define logic separately.
        """
        return isinstance(val, relations.ResourceRelatedField) and not isinstance(
            val, relations.SerializerMethodResourceRelatedField
        )

    def get_serializer(self, data, *args, **kwargs):
        # no data no wrapping needed
        if not data:
            return super().get_serializer(data, *args, **kwargs)

        many = kwargs.get("many")
        if not many:
            data = [data]

        # prefetch data for all related fields
        prefetch_per_field = {}
        serializer_class = self.get_serializer_class()
        for key, value in serializer_class._declared_fields.items():
            if self._is_related_field(value):
                source = value.source or key
                if many:
                    obj_ids = data.values_list(source, flat=True)
                else:
                    obj_ids = [data[0][source]]

                qs = value.model.objects.filter(id__in=obj_ids)
                qs = qs.select_related()
                if hasattr(self, "prefetch_related_for_field"):
                    qs = qs.prefetch_related(
                        *self.prefetch_related_for_field.get(source, [])
                    )

                objects = {obj.id: obj for obj in qs}
                prefetch_per_field[source] = objects

        # enhance entry dicts with model instances
        data = [
            AggregateObject(
                **{
                    **entry,
                    **{
                        field: objects[entry[field]]
                        for field, objects in prefetch_per_field.items()
                    },
                }
            )
            for entry in data
        ]

        if not many:
            data = data[0]

        return super().get_serializer(data, *args, **kwargs)
