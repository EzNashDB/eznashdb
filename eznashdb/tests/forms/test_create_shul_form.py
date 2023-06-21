from bs4 import BeautifulSoup
from django.urls import reverse

from eznashdb.forms import CreateShulForm
from eznashdb.models import Shul


def test_displays_shul_fields():
    form = CreateShulForm()
    soup = BeautifulSoup(form.as_p(), "html.parser")
    assert soup.find(attrs={"id": "id_name"})
    assert soup.find(attrs={"id": "id_has_female_leadership"})
    assert soup.find(attrs={"id": "id_has_childcare"})
    assert soup.find(attrs={"id": "id_can_say_kaddish"})


def test_creates_a_shul(client):
    client.post(
        reverse("eznashdb:create_shul"),
        data={
            "name": "test shul",
            "has_female_leadership": True,
            "has_childcare": True,
            "can_say_kaddish": True,
        },
    )
    assert Shul.objects.count() == 1


def test_redirects_to_shuls_list_view(client):
    response = client.post(
        reverse("eznashdb:create_shul"),
        data={
            "name": "test shul",
            "has_female_leadership": True,
            "has_childcare": True,
            "can_say_kaddish": True,
        },
        follow=True,
    )
    assert response.resolver_match.view_name == "eznashdb:shuls"
