from functools import lru_cache

from django import template
from django.contrib.staticfiles.finders import find
from django.utils.safestring import mark_safe

register = template.Library()


@lru_cache
def _read_static_file(path):
    with open(find(path)) as f:
        return f.read()


@register.simple_tag
def inline_svg(path):
    """Inline a static SVG's markup so CSS (e.g. currentColor) can style it."""
    return mark_safe(_read_static_file(path))
