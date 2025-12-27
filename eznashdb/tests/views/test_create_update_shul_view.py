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
    def shows_page_title(GET_request_create):
        response = CreateUpdateShulView.as_view()(GET_request_create)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert "add a shul" in soup.get_text().lower()

    def shows_form(GET_request_create):
        response = CreateUpdateShulView.as_view()(GET_request_create)
        soup = BeautifulSoup(str(response.render().content), features="html.parser")

        assert soup.find("form")


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

    def adds_rooms_to_shul(client, test_shul):
        data = {
            "name": test_shul.name,
            "address": test_shul.address,
            "latitude": test_shul.latitude,
            "longitude": test_shul.longitude,
            "address_changed": "false",
            **get_room_fields(room_index=0),
            **get_room_fields(room_index=1),
            **get_room_fs_metadata_fields(total_forms=2),
        }

        client.post(
            reverse("eznashdb:update_shul", kwargs={"pk": test_shul.pk}),
            data=data,
        )

        test_shul.refresh_from_db()
        assert test_shul.rooms.count() == 2

    def redirects_to_shuls_view(client, test_shul):
        response = client.post(
            reverse("eznashdb:update_shul", kwargs={"pk": test_shul.pk}),
            data={
                "name": test_shul.name,
                "address": test_shul.address,
                "latitude": test_shul.latitude,
                "longitude": test_shul.longitude,
                "address_changed": "false",
                **get_room_fields(room_index=0),
                **get_room_fs_metadata_fields(total_forms=1),
            },
        )
        redirect_url = response.headers.get("HX-Redirect")
        final_dest = client.get(redirect_url)
        assert final_dest.resolver_match.view_name == "eznashdb:shuls"


def test_lists_duplicates_if_any_found_and_address_changed(client):
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
            "submit_type": "main_submit",
            "wizard_step": "step1",  # Wizard step 1
            "address_changed": "true",
            **get_room_fields(room_index=0),
            **get_room_fs_metadata_fields(total_forms=1),
        },
        headers={"HX-Request": "true"},  # Simulate HTMX request
    )

    soup = BeautifulSoup(response.content, features="html.parser")

    # Check that modal is shown
    assert nearby_shul_1.name in str(soup)
    assert nearby_shul_2.name in str(soup)


def test_skips_duplicate_check_when_address_not_changed(client):
    # Create some nearby shuls
    nearby_shul_1 = Shul.objects.create(
        name="Nearby Shul 1",
        address="456 Nearby St",
        latitude=0.0005,
        longitude=0.0005,
    )
    nearby_shul_2 = Shul.objects.create(
        name="Nearby Shul 2",
        address="789 Adjacent Ave",
        latitude=-0.0008,
        longitude=-0.0003,
    )

    response = client.post(
        reverse("eznashdb:create_shul"),
        data={
            "name": "New Test Shul",
            "latitude": "0.0",
            "longitude": "0.0",
            "address": "123 Test St",
            "submit_type": "main_submit",
            "wizard_step": "step1",  # Wizard step 1
            "address_changed": "false",  # Address not changed
            **get_room_fields(room_index=0),
            **get_room_fs_metadata_fields(total_forms=1),
        },
        headers={"HX-Request": "true"},
    )

    # Should proceed to step 2 without showing modal
    soup = BeautifulSoup(response.content, features="html.parser")
    assert nearby_shul_1.name not in str(soup)
    assert nearby_shul_2.name not in str(soup)
    # Should show rooms section (step 2)
    assert "Rooms" in str(soup)


def test_skips_duplicate_check_when_submit_type_not_main_submit(client):
    # Create some nearby shuls
    nearby_shul_1 = Shul.objects.create(
        name="Nearby Shul 1",
        address="456 Nearby St",
        latitude=0.0005,
        longitude=0.0005,
    )

    response = client.post(
        reverse("eznashdb:create_shul"),
        data={
            "name": "New Test Shul",
            "latitude": "0.0",
            "longitude": "0.0",
            "address": "123 Test St",
            "submit_type": "other_submit",  # Not main_submit
            "wizard_step": "step1",  # Wizard step 1
            "address_changed": "true",
            **get_room_fields(room_index=0),
            **get_room_fs_metadata_fields(total_forms=1),
        },
        headers={"HX-Request": "true"},
    )

    # Should proceed to step 2 without showing modal (duplicate check skipped)
    soup = BeautifulSoup(response.content, features="html.parser")
    assert nearby_shul_1.name not in str(soup)
    # Should show rooms section (step 2)
    assert "Rooms" in str(soup)


def describe_wizard():
    """Tests for the two-step wizard flow for creating shuls"""

    def test_wizard_step1_transitions_to_step2(client):
        """Step 1 submission proceeds to step 2 without saving"""
        response = client.post(
            reverse("eznashdb:create_shul"),
            data={
                "name": "Test Shul",
                "address": "123 Test St",
                "latitude": "1.0",
                "longitude": "1.0",
                "submit_type": "main_submit",
                "wizard_step": "step1",
                "address_changed": "true",
            },
            headers={"HX-Request": "true"},
        )

        soup = BeautifulSoup(response.content, "html.parser")

        # Check step 2 is shown
        wizard_step_input = soup.find("input", {"name": "wizard_step"})
        assert wizard_step_input is not None
        assert wizard_step_input.get("value") == "step2", "Should transition to step 2"
        assert "Rooms" in str(soup)

        # Shul should NOT be saved yet
        assert Shul.objects.count() == 0

    def test_wizard_step2_saves_shul_and_rooms(client):
        """Step 2 submission saves shul and rooms in transaction"""
        # Submit step 2 directly (no session needed - all data in POST)
        response = client.post(
            reverse("eznashdb:create_shul"),
            data={
                "name": "Test Shul",
                "address": "123 Test St",
                "latitude": "1.0",
                "longitude": "1.0",
                "place_id": "test_place_id",
                "submit_type": "main_submit",
                "wizard_step": "step2",
                "address_changed": "false",
                **get_room_fields(room_index=0),
                **get_room_fs_metadata_fields(total_forms=1),
            },
            headers={"HX-Request": "true"},
        )

        # Shul should be saved
        assert Shul.objects.count() == 1
        shul = Shul.objects.first()
        assert shul.name == "Test Shul"

        # Room should be saved
        assert shul.rooms.count() == 1

        # Should redirect to map
        redirect_url = response.headers.get("HX-Redirect")
        assert redirect_url is not None
        assert "newShul" in redirect_url

    def test_wizard_step2_requires_at_least_one_room(client):
        """Step 2 validation enforces minimum 1 room for new shuls"""
        response = client.post(
            reverse("eznashdb:create_shul"),
            data={
                "name": "Test Shul",
                "address": "123 Test St",
                "latitude": "1.0",
                "longitude": "1.0",
                "place_id": "test_place_id",
                "wizard_step": "step2",
                "submit_type": "main_submit",
                "address_changed": "false",
                **get_room_fs_metadata_fields(total_forms=1),
                "rooms-0-name": "",
                "rooms-0-relative_size": "",
                "rooms-0-see_hear_score": "",
            },
            headers={"HX-Request": "true"},
        )

        soup = BeautifulSoup(response.content, "html.parser")

        # Should show validation error
        assert "Please add at least one room" in str(soup)

        # Shul should NOT be saved
        assert Shul.objects.count() == 0

    def test_wizard_step2_saves_address_changes(client):
        """Step 2 should save address changes made in step 2"""
        # Submit step 2 with address data
        client.post(
            reverse("eznashdb:create_shul"),
            data={
                "name": "Test Shul",
                "address": "Changed Address",
                "latitude": "2.0",
                "longitude": "2.0",
                "place_id": "changed_place_id",
                "submit_type": "main_submit",
                "wizard_step": "step2",
                "address_changed": "false",
                **get_room_fields(room_index=0),
                **get_room_fs_metadata_fields(total_forms=1),
            },
            headers={"HX-Request": "true"},
        )

        # Shul should be saved with the submitted address
        shul = Shul.objects.first()
        assert shul.address == "Changed Address"
        assert float(shul.latitude) == 2.0
        assert float(shul.longitude) == 2.0
        assert shul.place_id == "changed_place_id"

    def test_wizard_step2_checks_nearby_if_address_changed(client):
        """Step 2 should check for nearby shuls if address changed"""
        # Create a nearby shul
        nearby_shul = Shul.objects.create(
            name="Nearby Shul",
            address="Close Address",
            latitude=2.0005,  # Within 0.001 degrees of (2.0, 2.0)
            longitude=2.0005,
        )

        # Submit step 2 with address near the existing shul
        response = client.post(
            reverse("eznashdb:create_shul"),
            data={
                "name": "Test Shul",
                "address": "NEW ADDRESS",
                "latitude": "2.0",
                "longitude": "2.0",
                "place_id": "new_place_id",
                "submit_type": "main_submit",
                "wizard_step": "step2",
                "address_changed": "true",  # Trigger nearby check
                **get_room_fields(room_index=0),
                **get_room_fs_metadata_fields(total_forms=1),
            },
            headers={"HX-Request": "true"},
        )

        # Should show nearby shuls modal
        soup = BeautifulSoup(response.content, features="html.parser")
        assert nearby_shul.name in str(soup)
        assert "Nearby Shuls Found" in str(soup)

        # Shul should NOT be saved yet
        assert Shul.objects.filter(name="Test Shul").count() == 0

    def test_wizard_step2_nearby_modal_saves_when_user_continues(client):
        """Step 2 nearby shuls modal should save when user clicks 'Add New Anyway'"""
        # Create a nearby shul
        nearby_shul = Shul.objects.create(
            name="Nearby Shul",
            address="Close Address",
            latitude=2.0005,
            longitude=2.0005,
        )

        # First submit to get the modal
        response = client.post(
            reverse("eznashdb:create_shul"),
            data={
                "name": "Test Shul",
                "address": "NEW ADDRESS",
                "latitude": "2.0",
                "longitude": "2.0",
                "place_id": "new_place_id",
                "submit_type": "main_submit",
                "wizard_step": "step2",
                "address_changed": "true",
                **get_room_fields(room_index=0),
                **get_room_fs_metadata_fields(total_forms=1),
            },
            headers={"HX-Request": "true"},
        )

        # Modal should appear
        soup = BeautifulSoup(response.content, features="html.parser")
        assert nearby_shul.name in str(soup)

        # Now simulate clicking "Add New Anyway" - should save with wizard_step: "step2"
        response = client.post(
            reverse("eznashdb:create_shul"),
            data={
                "name": "Test Shul",
                "address": "NEW ADDRESS",
                "latitude": "2.0",
                "longitude": "2.0",
                "place_id": "new_place_id",
                "submit_type": "main_submit",
                "wizard_step": "step2",  # Same step, but address_changed: false to skip check
                "address_changed": "false",
                **get_room_fields(room_index=0),
                **get_room_fs_metadata_fields(total_forms=1),
            },
            headers={"HX-Request": "true"},
        )

        # Shul SHOULD be saved now
        assert Shul.objects.filter(name="Test Shul").count() == 1
        shul = Shul.objects.get(name="Test Shul")
        assert float(shul.latitude) == 2.0

        # Should redirect to map
        redirect_url = response.headers.get("HX-Redirect")
        assert redirect_url is not None
        assert "newShul" in redirect_url
