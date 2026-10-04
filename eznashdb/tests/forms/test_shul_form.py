import pytest
from bs4 import BeautifulSoup

from eznashdb.forms import ShulForm


def test_displays_shul_fields():
    form = ShulForm()
    soup = BeautifulSoup(form.as_p(), "html.parser")
    assert soup.find(attrs={"id": "id_name"})
    assert soup.find(attrs={"id": "id_address"})
    assert soup.find(attrs={"id": "id_latitude"})
    assert soup.find(attrs={"id": "id_longitude"})
    assert soup.find(attrs={"id": "id_place_id"})
    assert soup.find(attrs={"id": "id_zoom"})


def describe_validation():
    @pytest.mark.parametrize(
        ("lat", "lon", "is_valid"),
        [
            (None, None, False),
            (None, "1", False),
            ("1", None, False),
            ("1", "1", True),
            ("0", "0", True),
        ],
    )
    def lat_and_lon_are_required(lat, lon, is_valid):
        form = ShulForm(
            data={
                "name": "test shul",
                "address": "some address",
                "latitude": lat,
                "longitude": lon,
            }
        )
        assert form.is_valid() is is_valid


def describe_contact_field():
    def _valid_data(**extra):
        return {
            "name": "test shul",
            "address": "some address",
            "latitude": "1",
            "longitude": "1",
            **extra,
        }

    def is_optional():
        assert ShulForm(_valid_data()).is_valid()

    @pytest.mark.parametrize(
        ("contact", "is_valid"),
        [
            ("212-555-1234 ext. 5", True),
            ("rabbi@example.org", True),
            ("shul.org", True),
            ("hello", False),
        ],
    )
    def validates_the_value(contact, is_valid):
        assert ShulForm(_valid_data(contact=contact)).is_valid() is is_valid
