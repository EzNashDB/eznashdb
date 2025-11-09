from crispy_forms.helper import FormHelper
from django.db.models import Q
from django.utils.safestring import mark_safe
from django_filters import CharFilter, FilterSet

from eznashdb.constants import FieldsOptions
from eznashdb.enums import RelativeSize, RoomLayoutType, SeeHearScore
from eznashdb.filters import (
    BoolOrUnknownFilter,
    MultipleChoiceOrUnknownCharFilter,
    MultiSelectWithUnknownFilter,
)
from eznashdb.models import Shul


def x_help_text(help_text):
    """
    Add wrapper div to help text so it can respond to alpine.js
    """
    return mark_safe(f"""<div x-show="showHelpText" x-cloak x-transition>{help_text}</div>""")


class ShulFilterSet(FilterSet):
    name = CharFilter(lookup_expr="icontains", label=FieldsOptions.SHUL_NAME.label)
    can_say_kaddish = BoolOrUnknownFilter(
        model_field="can_say_kaddish",
        label=FieldsOptions.KADDISH.label,
        help_text=x_help_text(FieldsOptions.KADDISH.help_text),
    )
    rooms__relative_size = MultipleChoiceOrUnknownCharFilter(
        model_field="rooms__relative_size",
        choices=RelativeSize.choices,
        label=FieldsOptions.RELATIVE_SIZE.label,
        help_text=x_help_text(FieldsOptions.RELATIVE_SIZE.help_text),
        method="filter_rooms__relative_size",
    )
    rooms__see_hear_score = MultipleChoiceOrUnknownCharFilter(
        model_field="rooms__see_hear_score",
        choices=SeeHearScore.choices,
        label=FieldsOptions.SEE_HEAR.label,
        help_text=x_help_text(FieldsOptions.SEE_HEAR.help_text),
        method="filter_rooms__see_hear_score",
    )
    rooms__layout = MultiSelectWithUnknownFilter(
        choices=RoomLayoutType.choices,
        method="filter_room_layout",
        label=FieldsOptions.LAYOUT.label,
        help_text=x_help_text(FieldsOptions.LAYOUT.help_text),
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

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.form.helper = helper = FormHelper()
        helper.field_template = "bootstrap5/no_margin_field.html"
        helper.field_class = "input-group-sm"

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
            query |= Q(**all_False) | Q(rooms__isnull=True)
        return qs.filter(query).distinct()

    @property
    def qs(self):
        return super().qs.prefetch_related("rooms")

    class Meta:
        model = Shul
        fields = []
