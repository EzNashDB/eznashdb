from bs4 import BeautifulSoup

from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.forms import RoomForm
from eznashdb.models import Room, Shul


def test_displays_room_fields():
    form = RoomForm()
    soup = BeautifulSoup(form.as_p(), "html.parser")
    assert soup.find(attrs={"id": "id_name"})
    assert soup.find(attrs={"id": "id_relative_size"})
    assert soup.find(attrs={"id": "id_see_hear_score"})


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
