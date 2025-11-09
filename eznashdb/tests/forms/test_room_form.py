import pytest
from bs4 import BeautifulSoup

from eznashdb.enums import RelativeSize, RoomLayoutType, SeeHearScore
from eznashdb.forms import RoomForm
from eznashdb.models import Room, Shul


def test_displays_room_fields():
    form = RoomForm()
    soup = BeautifulSoup(form.as_p(), "html.parser")
    assert soup.find(attrs={"id": "id_name"})
    assert soup.find(attrs={"id": "id_relative_size"})
    assert soup.find(attrs={"id": "id_see_hear_score"})
    assert soup.find(attrs={"id": "id_layout"})


def test_saves_room():
    shul = Shul.objects.create()
    form = RoomForm(
        data={
            "shul": shul,
            "name": "test room",
            "relative_size": RelativeSize.M,
            "see_hear_score": SeeHearScore._3,
        }
    )
    form.save()

    room = Room.objects.first()
    assert room.shul == shul
    assert room.name == "test room"
    assert room.relative_size == RelativeSize.M
    assert room.see_hear_score == SeeHearScore._3


def describe_room_layout_field():
    @pytest.mark.parametrize(("field_name"), [layout_type.value for layout_type in RoomLayoutType])
    def saves_single_layout_type_to_field(field_name):
        shul = Shul.objects.create()
        form = RoomForm(
            data={
                "shul": shul,
                "name": "test room",
                "relative_size": RelativeSize.M,
                "see_hear_score": SeeHearScore._3,
                "layout": [field_name],
            }
        )
        form.save()

        room = Room.objects.first()
        assert getattr(room, field_name) is True

    def saves_multiple_layout_types_to_field():
        shul = Shul.objects.create()
        form = RoomForm(
            data={
                "shul": shul,
                "name": "test room",
                "relative_size": RelativeSize.M,
                "see_hear_score": SeeHearScore._3,
                "layout": [RoomLayoutType.is_elevated_back.value, RoomLayoutType.is_balcony.value],
            }
        )
        form.save()

        room = Room.objects.first()
        assert room.is_elevated_back is True
        assert room.is_balcony is True
