from django import template
from django.utils.safestring import mark_safe
register = template.Library()


@register.filter
def bool_to_icon(value: bool) -> str:
    icons = {
        True: "fa-check",
        False: "fa-times",
    }
    try:
        icon = icons[value]
    except KeyError:
        return value
    return mark_safe(
        f"<i class=\"fa {icon}\" aria-hidden=\"true\"></i>"
    )
