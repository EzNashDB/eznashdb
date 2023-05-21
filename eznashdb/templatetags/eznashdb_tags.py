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
    return mark_safe(f'<i class="fa {icon} w-12px text-center" aria-hidden="true"></i>')


EMPTY_STAR_HTML = '<i class="fa-regular fa-star"></i>'
FILLED_STAR_HTML = '<i class="fa-solid fa-star"></i>'


@register.filter
def score_to_stars(value) -> str:
    try:
        value = int(value)
    except TypeError:
        return value
    if not 1 <= value <= 5:
        return value
    stars = ""
    for _ in range(value):
        stars += FILLED_STAR_HTML
    for _ in range(5 - value):
        stars += EMPTY_STAR_HTML
    return mark_safe(f'<span class="text-nowrap text-warning">{stars}</span>')


ROOM_LAYOUT_DISPLAY_VALUES_BY_TYPE = {
    "Same floor": {
        "is_same_floor_side": "Side",
        "is_same_floor_back": "Back",
        "is_same_floor_elevated": "Elevated",
        "is_same_floor_level": "Level",
    },
    "Balcony": {
        "is_balcony": "",
    },
    "No women's section": {
        "is_only_men": "Only men",
        "is_mixed_seating": "Mixed seating",
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
        if len(display_values_dict.values()) == 1:
            return
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
