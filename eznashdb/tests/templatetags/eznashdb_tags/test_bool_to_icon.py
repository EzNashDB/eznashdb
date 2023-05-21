import pytest

from eznashdb.templatetags.eznashdb_tags import bool_to_icon


@pytest.mark.parametrize(
    "value,icon_class",
    [
        (True, "fa-check"),
        (False, "fa-times"),
    ],
)
def test_converts_bool_to_font_awesome_icon(value, icon_class):
    assert icon_class in bool_to_icon(value)


def test_passes_invalid_value_through():
    assert bool_to_icon("invalid") == "invalid"
