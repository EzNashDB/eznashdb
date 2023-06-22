from django import forms
from django.forms import ModelForm

from eznashdb.models import Shul


class CreateShulForm(ModelForm):
    room_name = forms.CharField(required=False)
    room_layout = forms.CharField(required=False)
    room_wheelchair_access = forms.CharField(required=False)
    room_see_hear = forms.CharField(required=False)

    class Meta:
        model = Shul
        fields = ["name", "has_female_leadership", "has_childcare", "can_say_kaddish"]
