from dataclasses import dataclass

from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

DEFAULT_ARG = object()


@dataclass()
class LabelWithIcon:
    label: str
    icon_class: str
    optional: bool = False

    @property
    def icon_html(self):
        return f"""
            <div class="d-inline-block w-min-25px">
                <i class="{self.icon_class}"></i>
            </div>
        """

    def __str__(self) -> str:
        label_html = f"""<span>{self.icon_html}{self.label}</span>"""
        if not self.optional:
            return mark_safe(label_html)
        # Pushed to the far end of the label line (see .form-label:has(.label-optional) in base.css)
        # so it reads as a note about the field, not as part of a question label. Translated here,
        # at render time, so it follows the active language.
        return format_html(
            '<span class="d-flex align-items-baseline gap-2">{}'
            '<span class="label-optional ms-auto small text-muted">{}</span></span>',
            mark_safe(label_html),
            gettext("Optional"),
        )

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

    @property
    def optional_form_label(self) -> LabelWithIcon:
        """The form label with a muted "Optional" at the end of its line."""
        return LabelWithIcon(self.verbose_label_text or self.label_text, self.icon_class, optional=True)


class FieldsOptions:
    SHUL_NAME = FieldOptions(_("Shul Name"), "fa-solid fa-synagogue")
    ADDRESS = FieldOptions(_("Address"), "fa-solid fa-location-dot")
    ROOM_NAME = FieldOptions(
        _("Room Name"),
        "fa-solid fa-tag",
        help_text=_("E.g. Main Sanctuary, Beit Midrash"),
    )
    RELATIVE_SIZE = FieldOptions(
        _("Size of Women's Section"),
        "fa-solid fa-up-right-and-down-left-from-center",
        verbose_label_text=_("How large is the women's section?"),
    )
    SEE_HEAR = FieldOptions(
        _("Visibility & Audibility"),
        "fa-solid fa-eye",
        verbose_label_text=_(
            "How well can you see and hear from the women's section, compared to the men's?"
        ),
    )
    KADDISH_POLICY = FieldOptions(
        _("Kaddish"),
        "fa-solid fa-comment",
        verbose_label_text=_("Can women say kaddish?"),
    )
    CONTACT = FieldOptions(
        _("Contact Info"),
        "fa-solid fa-address-book",
        verbose_label_text=_("Website, phone, or email"),
    )


JUST_SAVED_SHUL_SESSION_KEY = "just_saved_shul_id"
