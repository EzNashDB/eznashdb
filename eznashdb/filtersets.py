from django.db.models import Prefetch, Q
from django_filters import FilterSet

from eznashdb.constants import FieldsOptions
from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.filters import MultipleChoiceOrUnknownCharFilter, MultiSelectModelFieldFilter
from eznashdb.models import Room, Shul


class ShulFilterSet(FilterSet):
    rooms__relative_size = MultipleChoiceOrUnknownCharFilter(
        model_field="rooms__relative_size",
        choices=RelativeSize.choices,
        label=FieldsOptions.RELATIVE_SIZE.label,
        method="filter_rooms__relative_size",
    )
    rooms__see_hear_score = MultiSelectModelFieldFilter(
        model_field="rooms__see_hear_score",
        choices=SeeHearScore.choices,
        label=FieldsOptions.SEE_HEAR.label,
        method="filter_rooms__see_hear_score",
    )

    def filter_rooms__relative_size(self, qs, name, value):
        value = [x if x != "--" else "" for x in value]
        query = Q(rooms__relative_size__in=value)
        if "" in value:
            query |= Q(rooms__isnull=True)
        qs = qs.filter(query).distinct()
        return qs

    def filter_rooms__see_hear_score(self, qs, name, value):
        value = [x if x != "--" else "" for x in value]
        query = Q(rooms__see_hear_score__in=value)
        if "" in value:
            query |= Q(rooms__isnull=True)
        qs = qs.filter(query).distinct()
        return qs

    @property
    def qs(self):
        return super().qs.prefetch_related(Prefetch("rooms", queryset=Room.objects.all().order_by("pk")))

    class Meta:
        model = Shul
        fields = []
