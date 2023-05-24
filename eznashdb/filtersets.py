from django_filters import CharFilter, FilterSet

from eznashdb.filters import YesNoUnknownFilter
from eznashdb.models import Shul


class ShulFilterSet(FilterSet):
    name = CharFilter(lookup_expr="icontains", label="Shul Name")
    has_female_leadership = YesNoUnknownFilter(
        label="Female Leadership", model_field="has_female_leadership"
    )
    has_childcare = YesNoUnknownFilter(label="Childcare", model_field="has_childcare")
    can_say_kaddish = YesNoUnknownFilter(label="Kaddish", model_field="can_say_kaddish")

    class Meta:
        model = Shul
        fields = ["name", "has_female_leadership", "has_childcare"]
