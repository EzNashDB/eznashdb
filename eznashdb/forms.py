from crispy_forms.helper import FormHelper
from django import forms
from django.forms import HiddenInput, ModelForm, TextInput, inlineformset_factory

from eznashdb.choices import LAYOUT_CHOICES
from eznashdb.constants import LAYOUT_FIELDS, FieldsOptions
from eznashdb.enums import RoomLayoutType
from eznashdb.models import ChildcareProgram, Room, Shul, ShulLink
from eznashdb.widgets import MultiSelectWidget, NullableBooleanWidget


class ShulForm(ModelForm):
    has_no_childcare = forms.BooleanField(
        required=False, label="Shul has no children's programming on shabbat"
    )

    class Meta:
        model = Shul
        fields = [
            "name",
            "address",
            "has_female_leadership",
            "can_say_kaddish",
            "has_no_childcare",
            "latitude",
            "longitude",
            "place_id",
        ]
        labels = {
            "name": FieldsOptions.SHUL_NAME.label,
            "address": FieldsOptions.ADDRESS.label,
            "has_female_leadership": FieldsOptions.FEMALE_LEADERSHIP.label,
            "can_say_kaddish": FieldsOptions.KADDISH.label,
        }
        help_texts = {
            "has_female_leadership": FieldsOptions.FEMALE_LEADERSHIP.help_text,
            "can_say_kaddish": FieldsOptions.KADDISH.help_text,
        }
        widgets = {
            "has_female_leadership": NullableBooleanWidget(),
            "can_say_kaddish": NullableBooleanWidget(),
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
            "is_wheelchair_accessible",
            "see_hear_score",
        ]
        labels = {
            "name": FieldsOptions.ROOM_NAME.label,
            "relative_size": FieldsOptions.RELATIVE_SIZE.label,
            "see_hear_score": FieldsOptions.SEE_HEAR.label,
            "is_wheelchair_accessible": FieldsOptions.WHEELCHAIR_ACCESS.label,
        }
        help_texts = {
            "name": FieldsOptions.ROOM_NAME.help_text,
            "relative_size": FieldsOptions.RELATIVE_SIZE.help_text,
            "see_hear_score": FieldsOptions.SEE_HEAR.help_text,
            "is_wheelchair_accessible": FieldsOptions.WHEELCHAIR_ACCESS.help_text,
        }
        widgets = {
            "name": TextInput(attrs={"class": "fw-bold"}),
            "is_wheelchair_accessible": NullableBooleanWidget(),
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


class ShulLinkForm(ModelForm):
    class Meta:
        model = ShulLink
        fields = ["shul", "link"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper = FormHelper()
        helper.field_template = "bootstrap5/no_margin_field.html"
        helper.form_tag = False
        helper.disable_csrf = True
        helper.field_class = "w-100"
        self.helper.form_show_labels = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


class ChildcareProgramForm(ModelForm):
    class Meta:
        model = ChildcareProgram
        fields = ["shul", "name", "min_age", "max_age", "supervision_required", "duration"]
        labels = {
            "name": "Program Name",
            "min_age": "From Age",
            "max_age": "To Age",
            "supervision_required": "Parental Supervision",
        }
        widgets = {
            "name": TextInput(attrs={"class": "fw-bold"}),
            "supervision_required": NullableBooleanWidget(
                choices=((True, "Required"), (False, "Not required"))
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper = FormHelper()
        helper.template = "eznashdb/childcare_program_form.html"
        helper.form_tag = False
        helper.disable_csrf = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get("min_age")
        max_age = cleaned_data.get("max_age")
        if None not in [min_age, max_age] and min_age > max_age:
            self.add_error("min_age", "From Age must be less than To Age")


RoomFormSet = inlineformset_factory(
    Shul,
    Room,
    form=RoomForm,
    extra=1,
    can_delete=True,
    can_delete_extra=False,
)

ShulLinkFormSet = inlineformset_factory(
    Shul,
    ShulLink,
    form=ShulLinkForm,
    extra=1,
    can_delete=True,
    can_delete_extra=False,
)

ChildcareProgramFormSet = inlineformset_factory(
    Shul,
    ChildcareProgram,
    form=ChildcareProgramForm,
    extra=1,
    can_delete=True,
    can_delete_extra=False,
)
