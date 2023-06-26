from django import forms
from django.forms import ModelForm, inlineformset_factory

from eznashdb.models import Room, Shul


class CreateShulForm(ModelForm):
    class Meta:
        model = Shul
        fields = ["name", "has_female_leadership", "has_childcare", "can_say_kaddish"]


class RoomForm(ModelForm):
    id = forms.CharField(required=False)

    class Meta:
        model = Room
        fields = ["name"]
        labels = {"name": "Room Name"}


RoomFormSet = inlineformset_factory(
    Shul, Room, form=RoomForm, extra=1, can_delete=True, can_delete_extra=True
)
