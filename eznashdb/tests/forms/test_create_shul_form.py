from bs4 import BeautifulSoup

from eznashdb.forms import CreateShulForm


def test_displays_shul_fields():
    form = CreateShulForm()
    soup = BeautifulSoup(form.as_p(), "html.parser")
    assert soup.find(attrs={"id": "id_name"})
    assert soup.find(attrs={"id": "id_has_female_leadership"})
    assert soup.find(attrs={"id": "id_has_childcare"})
    assert soup.find(attrs={"id": "id_can_say_kaddish"})


def test_displays_room_fields():
    form = CreateShulForm()
    soup = BeautifulSoup(form.as_p(), "html.parser")
    assert soup.find(attrs={"id": "id_room_name"})
    assert soup.find(attrs={"id": "id_room_layout"})
    assert soup.find(attrs={"id": "id_room_wheelchair_access"})
    assert soup.find(attrs={"id": "id_room_see_hear"})
    assert soup.find(attrs={"id": "id_room_relative_size"})
