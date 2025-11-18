from dataclasses import dataclass

from django.utils.safestring import mark_safe

DEFAULT_ARG = object()


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

    @property
    def help_with_icon(self) -> str:
        return self.icon_class and LabelWithIcon(self.help_text, self.icon_class) or self.help_text


class FieldsOptions:
    SHUL_NAME = FieldOptions("Shul Name", "fa-solid fa-synagogue")
    ADDRESS = FieldOptions("Address", "fa-solid fa-location-dot")
    ROOM_NAME = FieldOptions(
        "Room Name",
        "fa-solid fa-tag",
        "Main Sanctuary, Beit Midrash, etc.",
    )
    RELATIVE_SIZE = FieldOptions(
        "Size <small>(vs Men's)</small>",
        "fa-solid fa-up-right-and-down-left-from-center",
        "How large is the women's section?",
    )
    SEE_HEAR = FieldOptions(
        "Visibility & Audibility <small>(vs Men's)</small>",
        "fa-solid fa-eye",
        """
            How well can women see and hear what happens at the bima, aron, and pulpit?
        """,
    )
