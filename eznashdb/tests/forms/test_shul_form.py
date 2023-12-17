from bs4 import BeautifulSoup

from eznashdb.forms import ShulForm


def test_displays_shul_fields():
    form = ShulForm()
    soup = BeautifulSoup(form.as_p(), "html.parser")
    assert soup.find(attrs={"id": "id_name"})
    assert soup.find(attrs={"id": "id_address"})
    assert soup.find(attrs={"id": "id_has_female_leadership"})
    assert soup.find(attrs={"id": "id_can_say_kaddish"})
    assert soup.find(attrs={"id": "id_latitude"})
    assert soup.find(attrs={"id": "id_longitude"})
    assert soup.find(attrs={"id": "id_place_id"})
