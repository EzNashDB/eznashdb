from django.db.models import Prefetch, Q
from django_filters import FilterSet, MultipleChoiceFilter
from waffle import flag_is_active

from eznashdb.constants import FieldsOptions
from eznashdb.enums import KaddishPolicy, RelativeSize, SeeHearScore
from eznashdb.filters import MultipleChoiceOrUnknownCharFilter, MultiSelectModelFieldFilter
from eznashdb.models import Room, Shul
from eznashdb.widgets import SearchableMultiTomSelectWidget


class ShulFilterSet(FilterSet):
    name = MultipleChoiceFilter(label=FieldsOptions.SHUL_NAME.filter_label)
    kaddish_policy = MultipleChoiceOrUnknownCharFilter(
        model_field="kaddish_policy",
        choices=KaddishPolicy.get_display_choices(include_blank=True),
        label=FieldsOptions.KADDISH_POLICY.filter_label,
        method="filter_kaddish_policy",
    )
    rooms__relative_size = MultipleChoiceOrUnknownCharFilter(
        model_field="rooms__relative_size",
        choices=RelativeSize.get_display_choices(include_blank=True),
        label=FieldsOptions.RELATIVE_SIZE.filter_label,
        method="filter_rooms__relative_size",
    )
    rooms__see_hear_score = MultiSelectModelFieldFilter(
        model_field="rooms__see_hear_score",
        choices=SeeHearScore.get_display_choices(include_blank=True),
        label=FieldsOptions.SEE_HEAR.filter_label,
        method="filter_rooms__see_hear_score",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not flag_is_active(self.request, "kaddish"):
            del self.filters["kaddish_policy"]

        names = Shul.objects.values_list("name", flat=True).distinct().order_by("name")
        choices = [(name, name) for name in names]
        self.filters["name"].extra["choices"] = choices
        self.form.fields["name"].choices = choices
        self.form.fields["name"].widget = SearchableMultiTomSelectWidget(choices=choices)

    def filter_kaddish_policy(self, qs, name, value):
        value = [x if x != "--" else "" for x in value]
        return qs.filter(kaddish_policy__in=value).distinct()

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
