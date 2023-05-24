from django_filters import CharFilter, FilterSet

from eznashdb.filters import YesNoUnsureFilter
from eznashdb.models import Shul


class ShulFilterSet(FilterSet):
    name = CharFilter(lookup_expr="icontains", label="Shul Name")
    has_female_leadership = YesNoUnsureFilter(
        label="Female Leadership", model_field="has_female_leadership"
    )
    has_childcare = YesNoUnsureFilter(label="Childcare", model_field="has_childcare")

    class Meta:
        model = Shul
        fields = ["name", "has_female_leadership", "has_childcare"]
