from django.forms import Select, SelectMultiple


class DataHtmlOptionMixin:
    """
    Mix-in: add a data-html attribute to each option. The value is the stringified
    label (what you would otherwise render as option innerHTML).

    Note: This is primarily to work around Firefox's behavior of stripping or
    normalizing HTML inside <option> elements. Firefox does not preserve
    option.innerHTML for markup, so we attach the intended HTML to a data-html
    attribute (which is preserved across browsers) so client-side scripts
    (e.g. TomSelect) can read and render it consistently.
    """

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )

        # Turn label into a string for the data attribute.
        # If your labels are already HTML (mark_safe), this will preserve that string.
        label_html = "" if label is None else str(label)

        # Ensure attrs dict exists and set data-html
        option.setdefault("attrs", {})
        option["attrs"]["data-html"] = label_html

        return option


class TomSelectMixin:
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["attrs"]["class"] += " tom-select"
        return context


class MultiTomSelectWidget(TomSelectMixin, DataHtmlOptionMixin, SelectMultiple):
    pass


class SingleTomSelectWidget(TomSelectMixin, DataHtmlOptionMixin, Select):
    pass


class NullableBooleanWidget(Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = kwargs.pop("choices", ((True, "Yes"), (False, "No")))
        self.choices = [(None, "---------"), *choices]
