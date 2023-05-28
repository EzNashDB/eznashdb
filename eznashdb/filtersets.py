from django.db.models import Q
from django_filters import CharFilter, FilterSet

from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.filters import (
    BoolOrUnknownFilter,
    MultipleChoiceOrUnknownCharFilter,
    TomSelectWithUnknownFilter,
)
from eznashdb.models import Shul


class ShulFilterSet(FilterSet):
    name = CharFilter(lookup_expr="icontains", label="Shul Name")
    has_female_leadership = BoolOrUnknownFilter(
        label="Female Leadership", model_field="has_female_leadership"
    )
    has_childcare = BoolOrUnknownFilter(label="Childcare", model_field="has_childcare")
    can_say_kaddish = BoolOrUnknownFilter(label="Kaddish", model_field="can_say_kaddish")
    rooms__is_wheelchair_accessible = BoolOrUnknownFilter(
        label="Wheelchair Access", model_field="rooms__is_wheelchair_accessible"
    )
    rooms__relative_size = MultipleChoiceOrUnknownCharFilter(
        label="Women's Section Size",
        model_field="rooms__relative_size",
        choices=[(choice.value, f"{choice.value} - {choice.label}") for choice in RelativeSize],
    )
    rooms__see_hear_score = MultipleChoiceOrUnknownCharFilter(
        label="Audibility / Visibility",
        model_field="rooms__see_hear_score",
        choices=[(choice.value, f"{choice.value} - {choice.label}") for choice in SeeHearScore],
    )
    rooms__layout = TomSelectWithUnknownFilter(
        label="Women's Section Location",
        choices=[
            ("is_same_floor_side", "Same floor - Side"),
            ("is_same_floor_back", "Same floor - Back"),
            ("is_same_floor_elevated", "Same floor - Elevated"),
            ("is_same_floor_level", "Same floor - Same height"),
            ("is_balcony", "Balcony"),
            ("is_only_men", "Only Men"),
            ("is_mixed_seating", "Mixed Seating"),
        ],
        method="filter_room_layout",
    )

    def filter_room_layout(self, qs, name, value):
        include_None = "--" in value
        values = [v for v in value if v != "--"]

        query = Q()
        layout_fields = [
            "is_same_floor_side",
            "is_same_floor_back",
            "is_same_floor_elevated",
            "is_same_floor_level",
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

    class Meta:
        model = Shul
        fields = []
