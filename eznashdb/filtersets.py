from django_filters import CharFilter, FilterSet

from eznashdb.models import Shul


class ShulFilterSet(FilterSet):
    name = CharFilter(lookup_expr="icontains", label="Name")

    class Meta:
        model = Shul
        fields = ["name"]
