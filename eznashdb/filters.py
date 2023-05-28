from typing import List, Tuple

from django.db.models import Q
from django_filters import MultipleChoiceFilter

from eznashdb.constants import DEFAULT_ARG
from eznashdb.widgets import TomSelectWidget


class TomSelectWithUnknownFilter(MultipleChoiceFilter):
    widget = TomSelectWidget

    def __init__(
        self, label, model_field, choices: List[Tuple[str, str]] = DEFAULT_ARG, *args, **kwargs
    ):
        if choices == DEFAULT_ARG:
            choices = self.choices
        choices.append(("--", "Unknown"))
        super().__init__(*args, widget=TomSelectWidget, choices=tuple(choices), label=label, **kwargs)
        self.model_field = model_field
        self.method = self.filter_method

    def filter_method(self, qs, name, value):
        raise NotImplementedError


class MultipleChoiceOrUnknownCharFilter(TomSelectWithUnknownFilter):
    def filter_method(self, qs, name, value):
        value = ["" if v == "--" else v for v in value]
        return qs.filter(**{f"{self.model_field}__in": value}).distinct()


class BoolOrUnknownFilter(TomSelectWithUnknownFilter):
    choices = [(True, "Yes"), (False, "No")]

    def filter_method(self, qs, name, value):
        include_None = "--" in value
        values = [v for v in value if v != "--"]

        query = Q(**{f"{self.model_field}__in": values})
        if include_None:
            query |= Q(**{f"{self.model_field}__isnull": True})
        return qs.filter(query).distinct()
