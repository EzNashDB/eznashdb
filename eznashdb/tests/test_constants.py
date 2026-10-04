from django.utils import translation
from django.utils.translation import gettext

from eznashdb.constants import FieldsOptions


def test_optional_marker_is_translated_when_rendered_not_when_defined():
    label = FieldsOptions.KADDISH_POLICY.optional_form_label

    with translation.override("he"):
        hebrew = gettext("Optional")
        assert hebrew != "Optional"
        assert hebrew in str(label)
