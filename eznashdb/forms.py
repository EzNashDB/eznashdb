from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout
from django import forms
from django.forms import ModelForm, inlineformset_factory

from eznashdb.constants import InputLabels
from eznashdb.enums import RoomLayoutType
from eznashdb.models import Room, Shul
from eznashdb.widgets import MultiSelectWidget, NullableBooleanWidget


class CreateShulForm(ModelForm):
    class Meta:
        model = Shul
        fields = ["name", "address", "has_female_leadership", "has_childcare", "can_say_kaddish"]
        labels = {
            "name": InputLabels.SHUL_NAME,
            "address": InputLabels.ADDRESS,
            "has_female_leadership": InputLabels.FEMALE_LEADERSHIP,
            "has_childcare": InputLabels.CHILDCARE,
            "can_say_kaddish": InputLabels.KADDISH,
        }
        widgets = {
            "has_female_leadership": NullableBooleanWidget(),
            "has_childcare": NullableBooleanWidget(),
            "can_say_kaddish": NullableBooleanWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper = FormHelper()
        helper.layout = Layout(HTML("{% include 'eznashdb/shul_form.html' %}"))
        helper.form_tag = False
        helper.field_class = "input-group input-group-sm"
        self.fields["name"].widget.attrs["class"] = "fw-bold"


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
        fields = ["shul", "name", "relative_size", "see_hear_score", "is_wheelchair_accessible"]
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
        helper.layout = Layout(HTML("{% include 'eznashdb/room_form.html' %}"))
        helper.form_tag = False
        helper.disable_csrf = True
        helper.field_class = "input-group input-group-sm"
        self.fields["name"].widget.attrs["class"] = "fw-bold"

    def save(self, commit=True):
        instance = super(RoomForm, self).save(commit=False)
        layout = self.cleaned_data["layout"]
        for layout_type in RoomLayoutType:
            setattr(instance, layout_type.value, layout_type.value in layout)
        if commit:
            instance.save()
        return instance


RoomFormSet = inlineformset_factory(
    Shul, Room, form=RoomForm, extra=1, can_delete=True, can_delete_extra=False
)
