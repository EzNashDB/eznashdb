from django import forms
from django.forms import ModelForm, inlineformset_factory

from eznashdb.enums import RoomLayoutType
from eznashdb.models import Room, Shul


class CreateShulForm(ModelForm):
    class Meta:
        model = Shul
        fields = ["name", "has_female_leadership", "has_childcare", "can_say_kaddish"]


class RoomForm(ModelForm):
    id = forms.CharField(required=False)
    layout = forms.MultipleChoiceField(
        required=False, label="Women's Section Location", choices=RoomLayoutType.choices
    )

    class Meta:
        model = Room
        fields = ["shul", "name", "relative_size", "see_hear_score", "is_wheelchair_accessible"]
        labels = {"name": "Room Name"}

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
