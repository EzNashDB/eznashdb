from crispy_forms.helper import FormHelper
from django import forms
from django.forms import HiddenInput, ModelForm, TextInput, inlineformset_factory

from eznashdb.constants import FieldsOptions
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
        if not (cleaned_data.get("latitude") and cleaned_data.get("longitude")):
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


RoomFormSet = inlineformset_factory(
    Shul,
    Room,
    form=RoomForm,
    extra=1,
    can_delete=True,
    can_delete_extra=False,
)
