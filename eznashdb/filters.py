from django.db.models import Q
from django_filters import MultipleChoiceFilter

from eznashdb.widgets import TomSelectWidget


class YesNoUnknownFilter(MultipleChoiceFilter):
    widget = TomSelectWidget

    def __init__(
        self,
        label,
        model_field,
        widget=TomSelectWidget,
        choices=(
            ("--", "Unknown"),
            (True, "Yes"),
            (False, "No"),
        ),
        *args,
        **kwargs,
    ):
        super().__init__(*args, widget=widget, choices=choices, label=label, **kwargs)
        self.model_field = model_field
        self.method = self.filter_method

    def filter_method(self, qs, name, value):
        include_None = "--" in value
        values = [v for v in value if v != "--"]

        query = Q(**{f"{self.model_field}__in": values})
        if include_None:
            query |= Q(**{f"{self.model_field}__isnull": True})
        return qs.filter(query).distinct()
