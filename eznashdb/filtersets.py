from django.db.models import Q
from django_filters import CharFilter, FilterSet, MultipleChoiceFilter

from eznashdb.models import Shul
from eznashdb.widgets import TomSelectWidget


class ShulFilterSet(FilterSet):
    name = CharFilter(lookup_expr="icontains", label="Shul Name")
    has_female_leadership = MultipleChoiceFilter(
        choices=(
            ("--", "Unknown"),
            (True, "Yes"),
            (False, "No"),
        ),
        widget=TomSelectWidget(),
        label="Female Leadership",
        method="filter_has_female_leadership",
    )

    def filter_has_female_leadership(self, qs, name, value):
        include_None = "--" in value
        values = [v for v in value if v != "--"]
        query = Q(has_female_leadership__in=values)
        if include_None:
            query |= Q(has_female_leadership__isnull=True)
        return qs.filter(query)

    class Meta:
        model = Shul
        fields = ["name", "has_female_leadership"]
