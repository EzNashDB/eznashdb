from django_filters import CharFilter, FilterSet

from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.filters import BoolOrUnknownFilter, MultipleChoiceOrUnknownCharFilter
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

    class Meta:
        model = Shul
        fields = []
