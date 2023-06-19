from django.db.models import Q
from django_filters import CharFilter, FilterSet

from eznashdb.constants import FilterHelpTexts
from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.filters import (
    BoolOrUnknownFilter,
    MultipleChoiceOrUnknownCharFilter,
    MultiSelectWithUnknownFilter,
    label_with_help_text,
)
from eznashdb.models import Shul


class ShulFilterSet(FilterSet):
    name = CharFilter(lookup_expr="icontains", label="Shul Name")
    not_city = CharFilter(lookup_expr="icontains", label="Not City")
    has_female_leadership = BoolOrUnknownFilter(
        label=label_with_help_text(
            label="Female Leadership", help_text=FilterHelpTexts.FEMALE_LEADERSHIP
        ),
        model_field="has_female_leadership",
    )
    has_childcare = BoolOrUnknownFilter(
        label=label_with_help_text(label="Childcare", help_text=FilterHelpTexts.CHILDCARE),
        model_field="has_childcare",
    )
    can_say_kaddish = BoolOrUnknownFilter(
        label=label_with_help_text(label="Kaddish", help_text=FilterHelpTexts.KADDISH),
        label_suffix="suffix",
        model_field="can_say_kaddish",
    )
    rooms__is_wheelchair_accessible = BoolOrUnknownFilter(
        label=label_with_help_text(
            label="Wheelchair Access", help_text=FilterHelpTexts.WHEELCHAIR_ACCESS
        ),
        model_field="rooms__is_wheelchair_accessible",
    )
    rooms__relative_size = MultipleChoiceOrUnknownCharFilter(
        label=label_with_help_text(
            label="Women's Section Size", help_text=FilterHelpTexts.RELATIVE_SIZE
        ),
        model_field="rooms__relative_size",
        choices=[(choice.value, f"{choice.value} - {choice.label}") for choice in RelativeSize],
    )
    rooms__see_hear_score = MultipleChoiceOrUnknownCharFilter(
        label=label_with_help_text(label="Audibility / Visibility", help_text=FilterHelpTexts.SEE_HEAR),
        model_field="rooms__see_hear_score",
        choices=[(choice.value, f"{choice.value} - {choice.label}") for choice in SeeHearScore],
    )
    rooms__layout = MultiSelectWithUnknownFilter(
        label=label_with_help_text(label="Women's Section Location", help_text=FilterHelpTexts.LAYOUT),
        choices=[
            ("is_same_height_side", "Same height - Side"),
            ("is_same_height_back", "Same height - Back"),
            ("is_elevated_side", "Elevated - Side"),
            ("is_elevated_back", "Elevated - Back"),
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

    class Meta:
        model = Shul
        fields = []
