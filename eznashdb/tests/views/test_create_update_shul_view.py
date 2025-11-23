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


def get_room_fields(room_index: int):
    return {
        f"rooms-{room_index}-id": "",
        f"rooms-{room_index}-shul": "",
        f"rooms-{room_index}-name": "test room 1",
        f"rooms-{room_index}-relative_size": "M",
        f"rooms-{room_index}-see_hear_score": "1",
    }


@pytest.fixture
def GET_request_create(rf_GET):
    return rf_GET("eznashdb:create_shul")


@pytest.fixture
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
            "name": "test shul",
            "address": "123 Sesame Street",
            "latitude": "1",
            "longitude": "1",
            **get_room_fields(room_index=0),
            **get_room_fields(room_index=1),
            **get_room_fs_metadata_fields(total_forms=2),
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
                "name": "test shul",
                "latitude": "1",
                "longitude": "1",
                "address": "some address",
                **get_room_fields(room_index=0),
                **get_room_fs_metadata_fields(total_forms=1),
            },
            follow=True,
        )
        assert response.resolver_match.view_name == "eznashdb:shuls"


def describe_update():
    def initializes_with_shul_and_room_data(GET_request_update, test_shul):
        room1 = test_shul.rooms.create(name="test room 1")
        room2 = test_shul.rooms.create(name="test room 2")

        response = CreateUpdateShulView.as_view()(GET_request_update(pk=test_shul.pk), pk=test_shul.pk)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        inputs = soup.find_all("input")
        input_values = {input_element.get("value") for input_element in inputs}
        assert test_shul.name in input_values
        assert room1.name in input_values
        assert room2.name in input_values


def test_lists_duplicates_if_any_found(client):
    # Create some nearby shuls
    nearby_shul_1 = Shul.objects.create(
        name="Nearby Shul 1",
        address="456 Nearby St",
        latitude=0.0005,  # Within 0.001 degrees
        longitude=0.0005,
    )
    nearby_shul_2 = Shul.objects.create(
        name="Nearby Shul 2",
        address="789 Adjacent Ave",
        latitude=-0.0008,  # Within 0.001 degrees
        longitude=-0.0003,
    )
    # Create a far away shul that should not be listed
    Shul.objects.create(
        name="Far Away Shul",
        address="999 Distant Dr",
        latitude=1.0,
        longitude=1.0,
    )

    response = client.post(
        reverse("eznashdb:create_shul"),
        data={
            "name": "New Test Shul",
            "latitude": "0.0",
            "longitude": "0.0",
            "address": "123 Test St",
            **get_room_fields(room_index=0),
            **get_room_fs_metadata_fields(total_forms=1),
        },
        headers={"HX-Request": "true"},  # Simulate HTMX request
    )

    soup = BeautifulSoup(response.content, features="html.parser")

    # Check that modal is shown
    assert nearby_shul_1.name in str(soup)
    assert nearby_shul_2.name in str(soup)
