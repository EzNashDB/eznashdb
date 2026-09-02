from collections.abc import Callable

from django_filters import MultipleChoiceFilter

from eznashdb.constants import DEFAULT_ARG
from eznashdb.widgets import MultiTomSelectWidget


class MultiSelectModelFieldFilter(MultipleChoiceFilter):
    def __init__(
        self,
        label,
        model_field,
        choices: list[tuple[str, str]] | Callable = DEFAULT_ARG,
        *args,
        **kwargs,
    ):
        widget = kwargs.pop("widget", MultiTomSelectWidget)
        # Pass a callable straight through rather than eagerly evaluating it here: Django's
        # ChoiceField wraps a callable in a CallableChoiceIterator and re-invokes it on every
        # render, so translated choice labels (gettext_lazy) resolve per-request instead of
        # being frozen in whatever language was active when this FilterSet class was first
        # imported.
        resolved_choices = choices if callable(choices) else tuple(choices)
        super().__init__(*args, choices=resolved_choices, label=label, widget=widget, **kwargs)
        self.model_field = model_field
        self.method = kwargs.pop("method", self.filter_method)

    def filter_method(self, qs, name, value):
        return qs.filter(**{f"{self.model_field}__in": value}).distinct()
