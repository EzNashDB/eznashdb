from crispy_forms.helper import FormHelper
from django import forms
from django.core.exceptions import ValidationError
from django.forms import HiddenInput, ModelForm, TextInput, inlineformset_factory
from django.forms.models import BaseInlineFormSet

from eznashdb.constants import FieldsOptions
from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.models import Room, Shul
from eznashdb.widgets import SingleTomSelectWidget


class ShulForm(ModelForm):
    class Meta:
        model = Shul
        fields = [
            "name",
            "address",
            "latitude",
            "longitude",
            "place_id",
        ]
        labels = {
            "name": FieldsOptions.SHUL_NAME.label,
            "address": FieldsOptions.ADDRESS.label,
        }
        widgets = {
            "latitude": HiddenInput(),
            "longitude": HiddenInput(),
            "place_id": HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper = FormHelper()
        helper.template = "eznashdb/shul_form.html"
        helper.form_tag = False
        self.fields["address"].required = True

    def clean(self):
        cleaned_data = super().clean()
        empty_values = [None, ""]
        if any(cleaned_data.get(field_name) in empty_values for field_name in ["latitude", "longitude"]):
            self.add_error("address", "Please select a valid address.")


class RoomForm(ModelForm):
    id = forms.CharField(required=False)

    class Meta:
        model = Room
        fields = [
            "shul",
            "name",
            "relative_size",
            "see_hear_score",
        ]
        labels = {
            "name": FieldsOptions.ROOM_NAME.label,
            "relative_size": FieldsOptions.RELATIVE_SIZE.help_with_icon,
            "see_hear_score": FieldsOptions.SEE_HEAR.help_with_icon,
        }
        help_texts = {
            "name": FieldsOptions.ROOM_NAME.help_text,
        }
        widgets = {
            "name": TextInput(attrs={"x-model": "roomName"}),
            "relative_size": SingleTomSelectWidget(),
            "see_hear_score": SingleTomSelectWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper = FormHelper()
        helper.template = "eznashdb/room_form.html"
        helper.form_tag = False
        helper.disable_csrf = True
        self.fields["relative_size"].choices = RelativeSize.get_display_choices(include_blank=True)
        self.fields["see_hear_score"].choices = SeeHearScore.get_display_choices(include_blank=True)


class BaseRoomFormSet(BaseInlineFormSet):
    """Custom formset that requires at least 1 room for new shuls only"""

    def clean(self):
        super().clean()
        # Only enforce minimum for new shuls (no pk yet)
        if not self.instance or not self.instance.pk:
            has_room = any(
                form.has_changed() and not form.cleaned_data.get("DELETE", False) for form in self.forms
            )
            if not has_room:
                raise ValidationError("Please add at least one room for this shul.")


RoomFormSet = inlineformset_factory(
    Shul,
    Room,
    form=RoomForm,
    formset=BaseRoomFormSet,
    extra=1,
    can_delete=True,
    can_delete_extra=False,
)
