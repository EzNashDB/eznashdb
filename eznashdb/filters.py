from django_filters import MultipleChoiceFilter

from eznashdb.constants import DEFAULT_ARG
from eznashdb.widgets import MultiTomSelectWidget


class MultiSelectModelFieldFilter(MultipleChoiceFilter):
    def __init__(
        self, label, model_field, choices: list[tuple[str, str]] = DEFAULT_ARG, *args, **kwargs
    ):
        widget = kwargs.pop("widget", MultiTomSelectWidget)
        super().__init__(*args, choices=tuple(choices), label=label, widget=widget, **kwargs)
        self.model_field = model_field
        self.method = kwargs.pop("method", self.filter_method)

    def filter_method(self, qs, name, value):
        return qs.filter(**{f"{self.model_field}__in": value}).distinct()
