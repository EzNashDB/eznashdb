from crispy_forms.helper import FormHelper
from django import forms
from django.forms import HiddenInput, ModelForm, inlineformset_factory

from eznashdb.choices import LAYOUT_CHOICES
from eznashdb.constants import LAYOUT_FIELDS, InputLabels
from eznashdb.enums import RoomLayoutType
from eznashdb.models import ChildcareProgram, Room, Shul, ShulLink
from eznashdb.widgets import MultiSelectWidget, NullableBooleanWidget


class ShulForm(ModelForm):
    has_no_childcare = forms.BooleanField(required=False)

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
            "name": InputLabels.SHUL_NAME,
            "has_female_leadership": InputLabels.FEMALE_LEADERSHIP,
            "can_say_kaddish": InputLabels.KADDISH,
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
        helper.field_template = "bootstrap5/no_margin_field.html"
        self.helper.form_show_labels = False
        helper.form_tag = False
        helper.field_class = "input-group input-group-sm"

    def clean(self):
        cleaned_data = super().clean()
        if not (cleaned_data.get("latitude") and cleaned_data.get("longitude")):
            self.add_error("address", "Please select a valid address.")


class RoomForm(ModelForm):
    id = forms.CharField(required=False)
    layout = forms.MultipleChoiceField(
        required=False,
        label=InputLabels.LAYOUT,
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
            "name": InputLabels.ROOM_NAME,
            "relative_size": InputLabels.RELATIVE_SIZE,
            "see_hear_score": InputLabels.SEE_HEAR,
            "is_wheelchair_accessible": InputLabels.WHEELCHAIR_ACCESS,
        }
        widgets = {
            "is_wheelchair_accessible": NullableBooleanWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper = FormHelper()
        helper.template = "eznashdb/room_form.html"
        helper.field_template = "bootstrap5/no_margin_field.html"
        helper.form_tag = False
        helper.disable_csrf = True
        helper.field_class = "input-group input-group-sm"
        self.helper.form_show_labels = False
        if self.instance.pk:
            self.initial["layout"] = [
                field for field in LAYOUT_FIELDS if getattr(self.instance, field, False)
            ]
        self.fields["layout"].choices = LAYOUT_CHOICES

    def save(self, commit=True):
        instance = super(RoomForm, self).save(commit=False)
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
        helper.field_class = "input-group input-group-sm w-100"
        self.helper.form_show_labels = False

    def save(self, commit=True):
        instance = super(ShulLinkForm, self).save(commit=False)
        if commit:
            instance.save()
        return instance


class ChildcareProgramForm(ModelForm):
    class Meta:
        model = ChildcareProgram
        fields = ["shul", "name", "min_age", "max_age", "supervision_required", "duration"]
        widgets = {
            "supervision_required": NullableBooleanWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper = FormHelper()
        helper.field_template = "bootstrap5/no_margin_field.html"
        helper.template = "eznashdb/childcare_program_form.html"
        helper.form_tag = False
        helper.disable_csrf = True
        helper.field_class = "input-group input-group-sm"
        self.helper.form_show_labels = False

    def save(self, commit=True):
        instance = super(ChildcareProgramForm, self).save(commit=False)
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
