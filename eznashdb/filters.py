from typing import List, Tuple

from django.db.models import Q
from django_filters import MultipleChoiceFilter

from eznashdb.constants import DEFAULT_ARG
from eznashdb.widgets import MultiSelectWidget


class MultiSelectWithUnknownFilter(MultipleChoiceFilter):
    def __init__(self, label, choices: List[Tuple[str, str]] = DEFAULT_ARG, *args, **kwargs):
        if choices == DEFAULT_ARG:
            choices = getattr(self, "choices", [])
        choices.insert(0, ("--", "Unknown"))
        super().__init__(*args, widget=MultiSelectWidget, choices=tuple(choices), label=label, **kwargs)


class MultiSelectModelFieldWithUnknownFilter(MultiSelectWithUnknownFilter):
    def __init__(
        self, label, model_field, choices: List[Tuple[str, str]] = DEFAULT_ARG, *args, **kwargs
    ):
        super().__init__(label, choices, *args, **kwargs)
        self.model_field = model_field
        self.method = self.filter_method

    def filter_method(self, qs, name, value):
        raise NotImplementedError


class MultipleChoiceOrUnknownCharFilter(MultiSelectModelFieldWithUnknownFilter):
    def filter_method(self, qs, name, value):
        value = ["" if v == "--" else v for v in value]
        return qs.filter(**{f"{self.model_field}__in": value}).distinct()


class BoolOrUnknownFilter(MultiSelectModelFieldWithUnknownFilter):
    def __init__(self, label, model_field, *args, **kwargs):
        self.choices = [(True, "Yes"), (False, "No")]
        super().__init__(label, model_field, *args, **kwargs)

    def filter_method(self, qs, name, value):
        include_None = "--" in value
        values = [v for v in value if v != "--"]

        query = Q(**{f"{self.model_field}__in": values})
        if include_None:
            query |= Q(**{f"{self.model_field}__isnull": True})
        return qs.filter(query).distinct()
