from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.forms import ModelForm

from eznashdb.models import Shul


class CreateShulForm(ModelForm):
    class Meta:
        model = Shul
        fields = ["name", "has_female_leadership", "has_childcare", "can_say_kaddish"]

    helper = FormHelper()
    helper.add_input(Submit("submit", "Submit", css_class="btn-primary"))
