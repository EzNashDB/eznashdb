from dataclasses import dataclass

from django.utils.safestring import mark_safe

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
class LabelWithIcon:
    label: str
    icon_class: str

    @property
    def icon_html(self):
        return f"""
            <div class="d-inline-block w-min-25px">
                <i class="{self.icon_class}"></i>
            </div>
        """

    def __str__(self) -> str:
        return mark_safe(f"""<span>{self.icon_html}{self.label}</span>""")

    def __getitem__(self, item):
        return str(self)[item]


@dataclass()
class FieldOptions:
    label_str: str = ""
    icon_class: str = ""
    help_text: str = ""

    @property
    def label(self) -> str:
        return self.icon_class and LabelWithIcon(self.label_str, self.icon_class) or self.label_str


class FieldsOptions:
    SHUL_NAME = FieldOptions("Name", "fa-solid fa-synagogue")
    ADDRESS = FieldOptions("Address", "fa-solid fa-location-dot")
    ROOM_NAME = FieldOptions(
        "Room Name",
        "fa-solid fa-tag",
        "Main Sanctuary, Beit Midrash, etc.",
    )
    CHILDCARE = FieldOptions(
        "Childcare & Youth Programming",
        "fa-solid fa-child-reaching",
    )
    LINKS = FieldOptions(
        "Links",
        "fa-solid fa-link",
    )
    RELATIVE_SIZE = FieldOptions(
        "Size",
        "fa-solid fa-up-right-and-down-left-from-center",
        "How large is the women's section?",
    )
    SEE_HEAR = FieldOptions(
        "Visibility & Audibility",
        "fa-solid fa-eye",
        """
            How well you can see and hear what is happening at the bima, aron, and pulpit
            from the women's section?
        """,
    )
    LAYOUT = FieldOptions(
        "Layout",
        "fa-solid fa-cubes",
        "Where is the women's section located?",
    )
