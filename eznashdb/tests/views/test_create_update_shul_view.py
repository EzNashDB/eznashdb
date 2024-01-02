from functools import partial

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from eznashdb.models import Shul
from eznashdb.views import CreateUpdateShulView

# Helpers


def get_fs_metadata_fields(
    prefix: str = "rooms",
    initial_forms: int = 0,
    max_num_forms: int = 1000,
    min_num_forms: int = 0,
    total_forms: int = 0,
) -> dict:
    """
    Returns a dict representing the hidden metadata fields for a formset
    """
    return {
        f"{prefix}-INITIAL_FORMS": str(initial_forms),
        f"{prefix}-MAX_NUM_FORMS": str(max_num_forms),
        f"{prefix}-MIN_NUM_FORMS": str(min_num_forms),
        f"{prefix}-TOTAL_FORMS": str(total_forms),
    }


get_room_fs_metadata_fields = partial(get_fs_metadata_fields, prefix="rooms")
get_link_fs_metadata_fields = partial(get_fs_metadata_fields, prefix="shul-links")
get_childcare_fs_metadata_fields = partial(get_fs_metadata_fields, prefix="childcare-programs")


def get_room_fields(room_index: int):
    return {
        f"rooms-{room_index}-id": "",
        f"rooms-{room_index}-shul": "",
        f"rooms-{room_index}-name": "test room 1",
        f"rooms-{room_index}-relative_size": "M",
        f"rooms-{room_index}-see_hear_score": "1",
        f"rooms-{room_index}-is_wheelchair_accessible": "true",
    }


@pytest.fixture()
def GET_request_create(rf_GET):
    return rf_GET("eznashdb:create_shul")


@pytest.fixture()
def GET_request_update(rf_GET):
    def _generate_request(**params):
        return rf_GET("eznashdb:update_shul", params)

    return _generate_request


# Tests


def describe_create():
    def test_shows_page_title(GET_request_create):
        response = CreateUpdateShulView.as_view()(GET_request_create)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert "add a shul" in soup.get_text().lower()

    def test_shows_form(GET_request_create):
        response = CreateUpdateShulView.as_view()(GET_request_create)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert soup.find("form")

    def test_creates_shul_with_rooms(client):
        data = {
            "can_say_kaddish": "unknown",
            "has_female_leadership": "unknown",
            "name": "test shul",
            "address": "123 Sesame Street",
            "latitude": "1",
            "longitude": "1",
            **get_room_fields(room_index=0),
            **get_room_fields(room_index=1),
            **get_room_fs_metadata_fields(total_forms=2),
            **get_link_fs_metadata_fields(),
            **get_childcare_fs_metadata_fields(),
        }

        client.post(
            reverse("eznashdb:create_shul"),
            data=data,
        )
        assert Shul.objects.count() == 1
        assert Shul.objects.first().rooms.count() == 2

    def test_redirects_to_shuls_list_view(client):
        response = client.post(
            reverse("eznashdb:create_shul"),
            data={
                "can_say_kaddish": "unknown",
                "has_female_leadership": "unknown",
                "name": "test shul",
                "latitude": "1",
                "longitude": "1",
                **get_room_fields(room_index=0),
                **get_room_fs_metadata_fields(total_forms=1),
                **get_link_fs_metadata_fields(),
                **get_childcare_fs_metadata_fields(),
            },
            follow=True,
        )
        assert response.resolver_match.view_name == "eznashdb:shuls"


def describe_update():
    def initializes_with_shul_and_room_data(GET_request_update):
        shul = Shul.objects.create(name="test shul")
        room1 = shul.rooms.create(name="test room 1")
        room2 = shul.rooms.create(name="test room 2")

        response = CreateUpdateShulView.as_view()(GET_request_update(pk=shul.pk), pk=shul.pk)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        inputs = soup.find_all("input")
        input_values = {input_element.get("value") for input_element in inputs}
        assert shul.name in input_values
        assert room1.name in input_values
        assert room2.name in input_values
