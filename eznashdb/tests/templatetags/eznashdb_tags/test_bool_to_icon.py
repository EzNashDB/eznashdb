from eznashdb.templatetags.eznashdb_tags import bool_to_icon
import pytest

@pytest.mark.parametrize(
    "value,icon",
    [
        (True, "fa-check"),
        (False, "fa-times"),
    ],
)
def test_converts_bool_to_font_awesome_icon(value, icon):
    icon_html = f"<i class=\"fa {icon}\" aria-hidden=\"true\"></i>"
    assert bool_to_icon(value) == icon_html

def test_passes_invalid_value_through():
    assert bool_to_icon("invalid") == "invalid"
