from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout
from django import forms
from django.forms import ModelForm, inlineformset_factory

from eznashdb.constants import FilterHelpTexts
from eznashdb.enums import RoomLayoutType
from eznashdb.filters import label_with_help_text
from eznashdb.models import Room, Shul
from eznashdb.widgets import MultiSelectWidget


class CreateShulForm(ModelForm):
    class Meta:
        model = Shul
        fields = ["name", "has_female_leadership", "has_childcare", "can_say_kaddish"]
        labels = {
            "name": "Shul Name",
            "has_female_leadership": label_with_help_text(
                label="Female Leadership", help_text=FilterHelpTexts.FEMALE_LEADERSHIP
            ),
            "has_childcare": label_with_help_text(
                label="Childcare", help_text=FilterHelpTexts.CHILDCARE
            ),
            "can_say_kaddish": label_with_help_text(label="Kaddish", help_text=FilterHelpTexts.KADDISH),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper = FormHelper()
        helper.layout = Layout(HTML("{% include 'eznashdb/shul_form.html' %}"))
        helper.form_tag = False
        helper.field_class = "input-group input-group-sm"


class RoomForm(ModelForm):
    id = forms.CharField(required=False)
    layout = forms.MultipleChoiceField(
        required=False,
        label="Women's Section Location",
        choices=RoomLayoutType.choices,
        widget=MultiSelectWidget(),
    )

    class Meta:
        model = Room
        fields = ["shul", "name", "relative_size", "see_hear_score", "is_wheelchair_accessible"]
        labels = {"name": "Room Name"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = helper = FormHelper()
        helper.layout = Layout(HTML("{% include 'eznashdb/room_form.html' %}"))
        helper.form_tag = False
        helper.disable_csrf = True
        helper.field_class = "input-group input-group-sm"

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
