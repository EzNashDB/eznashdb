from bs4 import BeautifulSoup

from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.forms import RoomForm, RoomFormSet
from eznashdb.models import Room


def test_displays_room_fields():
    form = RoomForm()
    soup = BeautifulSoup(form.as_p(), "html.parser")
    assert soup.find(attrs={"id": "id_name"})
    assert soup.find(attrs={"id": "id_relative_size"})
    assert soup.find(attrs={"id": "id_see_hear_score"})


def test_saves_room(test_shul):
    form = RoomForm(
        data={
            "shul": test_shul,
            "name": "test room",
            "relative_size": RelativeSize.M,
            "see_hear_score": SeeHearScore._3,
        }
    )
    form.save()

    room = Room.objects.first()
    assert room.shul == test_shul
    assert room.name == "test room"
    assert room.relative_size == RelativeSize.M
    assert room.see_hear_score == SeeHearScore._3


def test_room_formset_requires_minimum_for_new_shuls():
    """New shuls must have at least 1 room"""
    formset = RoomFormSet(
        data={
            "rooms-TOTAL_FORMS": "1",
            "rooms-INITIAL_FORMS": "0",
            "rooms-MIN_NUM_FORMS": "0",
            "rooms-MAX_NUM_FORMS": "1000",
            "rooms-0-name": "",
            "rooms-0-relative_size": "",
            "rooms-0-see_hear_score": "",
        },
        instance=None,  # No instance = new shul
    )
    assert not formset.is_valid()
    assert "Please add at least one room" in str(formset.non_form_errors())


def test_room_formset_accepts_valid_room_for_new_shul():
    """New shuls can be saved with at least 1 valid room"""
    formset = RoomFormSet(
        data={
            "rooms-TOTAL_FORMS": "1",
            "rooms-INITIAL_FORMS": "0",
            "rooms-MIN_NUM_FORMS": "0",
            "rooms-MAX_NUM_FORMS": "1000",
            "rooms-0-name": "Main Sanctuary",
            "rooms-0-relative_size": RelativeSize.M,
            "rooms-0-see_hear_score": SeeHearScore._3,
        },
        instance=None,  # No instance = new shul
    )
    assert formset.is_valid()


def test_room_formset_allows_zero_rooms_for_existing_shuls(test_shul):
    """Existing shuls can have 0 rooms (backward compatibility)"""
    formset = RoomFormSet(
        data={
            "rooms-TOTAL_FORMS": "0",
            "rooms-INITIAL_FORMS": "0",
            "rooms-MIN_NUM_FORMS": "0",
            "rooms-MAX_NUM_FORMS": "1000",
        },
        instance=test_shul,  # Has instance = existing shul
    )
    assert formset.is_valid()
