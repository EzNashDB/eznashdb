from django.db.models import Q
from django_filters import CharFilter, FilterSet

from eznashdb.constants import InputLabels
from eznashdb.enums import RelativeSize, RoomLayoutType, SeeHearScore
from eznashdb.filters import (
    BoolOrUnknownFilter,
    MultipleChoiceOrUnknownCharFilter,
    MultiSelectWithUnknownFilter,
)
from eznashdb.models import Shul


class ShulFilterSet(FilterSet):
    name = CharFilter(lookup_expr="icontains", label=InputLabels.SHUL_NAME)
    has_female_leadership = BoolOrUnknownFilter(
        label=InputLabels.FEMALE_LEADERSHIP, model_field="has_female_leadership"
    )
    can_say_kaddish = BoolOrUnknownFilter(
        label=InputLabels.KADDISH, label_suffix="suffix", model_field="can_say_kaddish"
    )
    rooms__is_wheelchair_accessible = BoolOrUnknownFilter(
        label=InputLabels.WHEELCHAIR_ACCESS, model_field="rooms__is_wheelchair_accessible"
    )
    rooms__relative_size = MultipleChoiceOrUnknownCharFilter(
        label=InputLabels.RELATIVE_SIZE,
        model_field="rooms__relative_size",
        choices=[(choice.value, f"{choice.value} - {choice.label}") for choice in RelativeSize],
    )
    rooms__see_hear_score = MultipleChoiceOrUnknownCharFilter(
        label=InputLabels.SEE_HEAR,
        model_field="rooms__see_hear_score",
        choices=SeeHearScore.choices,
    )
    rooms__layout = MultiSelectWithUnknownFilter(
        label=InputLabels.LAYOUT, choices=RoomLayoutType.choices, method="filter_room_layout"
    )

    def filter_room_layout(self, qs, name, value):
        include_None = "--" in value
        values = [v for v in value if v != "--"]

        query = Q()
        layout_fields = [
            "is_same_height_side",
            "is_same_height_back",
            "is_elevated_side",
            "is_elevated_back",
            "is_balcony",
            "is_only_men",
            "is_mixed_seating",
        ]
        for field in layout_fields:
            if field in values:
                query |= Q(**{f"rooms__{field}": True})
        if include_None:
            all_False = {f"rooms__{field}": False for field in layout_fields}
            query |= Q(**all_False)
        return qs.filter(query).distinct()

    @property
    def qs(self):
        return super().qs.prefetch_related("rooms")

    class Meta:
        model = Shul
        fields = []
