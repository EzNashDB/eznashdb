from django.forms import SelectMultiple


class MultiSelectWidget(SelectMultiple):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["attrs"]["class"] = "bs-multiselect"
        return context
