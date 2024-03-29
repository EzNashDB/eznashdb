from dataclasses import dataclass

DEFAULT_ARG = object()

LAYOUT_FIELDS = [
    "is_same_height_side",
    "is_same_height_back",
    "is_elevated_side",
    "is_elevated_back",
    "is_balcony",
    "is_only_men",
    "is_mixed_seating",
]


@dataclass()
class LabelWithHelpText:
    label: str = ""
    help_text: str = ""
    icon_class: str = ""

    def __str__(self) -> str:
        return self.label

    def __getitem__(self, item):
        return str(self)[item]


class InputLabels:
    SHUL_NAME = "Name*"
    ROOM_NAME = LabelWithHelpText(
        "Room Name*",
        "Main Sanctuary, Beit Midrash, etc.",
        "fa-solid fa-home",
    )
    FEMALE_LEADERSHIP = LabelWithHelpText(
        "Female Leadership",
        """
            Are there any women in leadership positions (president, executive director,
            halachic/spiritual leader, gabbai't, etc.)?
        """,
        "fa-solid fa-user-shield",
    )
    CHILDCARE = LabelWithHelpText(
        "Childcare", "Is there an on-site childcare program?", "fa-solid fa-child-reaching"
    )
    KADDISH = LabelWithHelpText("Kaddish", "Can women say kaddish?", "fa-solid fa-comment")
    WHEELCHAIR_ACCESS = LabelWithHelpText(
        "Wheelchair Access", "Is the women's section wheelchair accessible?", "fa-solid fa-wheelchair"
    )
    RELATIVE_SIZE = LabelWithHelpText(
        "Size",
        "How large is the women's section relative to the men's section?",
        "fa-solid fa-up-right-and-down-left-from-center",
    )
    SEE_HEAR = LabelWithHelpText(
        "Visibility + Audibility",
        """
            On a 1-5 scale, how well you can see and hear what is happening at the bima, aron, and pulpit
            from the women's section, relative to the men's section?
        """,
        "fa-solid fa-eye",
    )
    LAYOUT = LabelWithHelpText(
        "Layout",
        "Where is the women's section located?",
        "fa-solid fa-cubes",
    )


BASE_OSM_URL = "https://nominatim.openstreetmap.org/"
