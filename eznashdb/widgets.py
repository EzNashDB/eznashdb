from django.forms import Select, SelectMultiple


class MultiSelectWidget(SelectMultiple):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["attrs"]["class"] = "tom-select form-control"
        return context


class NullableBooleanWidget(Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = kwargs.pop("choices", ((True, "Yes"), (False, "No")))
        self.choices = [(None, "---------"), *choices]
