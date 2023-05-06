from dataclasses import dataclass
from typing import List
from django import template
from django.utils.safestring import mark_safe

from eznashdb.models import Room

register = template.Library()


@register.filter
def bool_to_icon(value: bool) -> str:
    icons = {
        True: "fa-check text-bold",
        False: "fa-times text-bold",
    }
    try:
        icon = icons[value]
    except KeyError:
        return value
    return mark_safe(f'<i class="fa {icon}" aria-hidden="true"></i>')


ROOM_LAYOUT_DISPLAY_VALUES_BY_TYPE = {
    "Balcony": {
        "is_balcony_side": "Side",
        "is_balcony_back": "Back",
    },
    "Same floor": {
        "is_centered": "Centered Mechitza",
        "is_same_floor_side": "Side",
        "is_same_floor_back": "Back",
        "is_same_floor_elevated": "Elevated",
        "is_same_floor_level": "Level",
    },
    "No women's section": {
        "is_only_men": "Only Men",
        "is_mixed_seating": "Mixed Seating",
    },
}


@dataclass
class RoomLayoutTypeDisplayData:
    room: Room
    layout_type: str

    @property
    def as_bool(self):
        return any(
            getattr(self.room, field)
            for field in ROOM_LAYOUT_DISPLAY_VALUES_BY_TYPE[self.layout_type].keys()
        )

    @property
    def as_string(self) -> str:
        display_values_dict = ROOM_LAYOUT_DISPLAY_VALUES_BY_TYPE[self.layout_type]
        display_values = [
            v for k, v in display_values_dict.items() if getattr(self.room, k)
        ]
        return ", ".join(display_values)


@register.filter
def get_layout_type_display_data_list(room: Room) -> List[RoomLayoutTypeDisplayData]:
    return [
        RoomLayoutTypeDisplayData(room, layout_type)
        for layout_type in ROOM_LAYOUT_DISPLAY_VALUES_BY_TYPE
    ]
