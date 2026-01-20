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
