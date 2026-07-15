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
    label_text: str = ""
    icon_class: str = ""
    help_text: str = ""
    verbose_label_text: str = ""

    def _with_icon(self, text: str) -> str:
        return self.icon_class and LabelWithIcon(text, self.icon_class) or text

    @property
    def filter_label(self) -> str:
        return self._with_icon(self.label_text)

    @property
    def form_label(self) -> str:
        return self._with_icon(self.verbose_label_text or self.label_text)


class FieldsOptions:
    SHUL_NAME = FieldOptions("Shul Name", "fa-solid fa-synagogue")
    ADDRESS = FieldOptions("Address", "fa-solid fa-location-dot")
    ROOM_NAME = FieldOptions(
        "Room Name",
        "fa-solid fa-tag",
        help_text="Main Sanctuary, Beit Midrash, etc.",
    )
    RELATIVE_SIZE = FieldOptions(
        "Size of Women's Section",
        "fa-solid fa-up-right-and-down-left-from-center",
        verbose_label_text="How large is the women's section?",
    )
    SEE_HEAR = FieldOptions(
        "Visibility & Audibility",
        "fa-solid fa-eye",
        verbose_label_text="""
            Compared to men, how well can women see and hear?
        """,
    )
    KADDISH_POLICY = FieldOptions(
        "Kaddish",
        "fa-solid fa-comment",
        verbose_label_text="Can women say kaddish?",
    )


JUST_SAVED_SHUL_SESSION_KEY = "just_saved_shul_id"
