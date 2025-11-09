from crispy_forms.helper import FormHelper
from django import forms
from django.forms import HiddenInput, ModelForm, TextInput, inlineformset_factory

from eznashdb.choices import LAYOUT_CHOICES
from eznashdb.constants import LAYOUT_FIELDS, FieldsOptions
from eznashdb.enums import RoomLayoutType
from eznashdb.models import Room, Shul
from eznashdb.widgets import MultiSelectWidget


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
    layout = forms.MultipleChoiceField(
        required=False,
        label=FieldsOptions.LAYOUT.label,
        help_text=FieldsOptions.LAYOUT.help_text,
        choices=RoomLayoutType.choices,
        widget=MultiSelectWidget(),
    )

    class Meta:
        model = Room
        fields = [
            "shul",
            "name",
            "layout",
            "relative_size",
            "see_hear_score",
        ]
        labels = {
            "name": FieldsOptions.ROOM_NAME.label,
            "relative_size": FieldsOptions.RELATIVE_SIZE.label,
            "see_hear_score": FieldsOptions.SEE_HEAR.label,
        }
        help_texts = {
            "name": FieldsOptions.ROOM_NAME.help_text,
            "relative_size": FieldsOptions.RELATIVE_SIZE.help_text,
            "see_hear_score": FieldsOptions.SEE_HEAR.help_text,
        }
        widgets = {
            "name": TextInput(attrs={"class": "fw-bold"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper = FormHelper()
        helper.template = "eznashdb/room_form.html"
        helper.form_tag = False
        helper.disable_csrf = True
        if self.instance.pk:
            self.initial["layout"] = [
                field for field in LAYOUT_FIELDS if getattr(self.instance, field, False)
            ]
        self.fields["layout"].choices = LAYOUT_CHOICES

    def save(self, commit=True):
        instance = super().save(commit=False)
        layout = self.cleaned_data["layout"]
        for layout_type in RoomLayoutType:
            setattr(instance, layout_type.value, layout_type.value in layout)
        if commit:
            instance.save()
        return instance


RoomFormSet = inlineformset_factory(
    Shul,
    Room,
    form=RoomForm,
    extra=1,
    can_delete=True,
    can_delete_extra=False,
)
