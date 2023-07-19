from dataclasses import dataclass

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

DEFAULT_ARG = object()


@dataclass()
class LabelWithHelpText:
    label: str = ""
    help_text: str = ""

    def __str__(self) -> str:
        context = {"label": mark_safe(self.label), "help_text": mark_safe(self.help_text)}
        return render_to_string("eznashdb/includes/filter_label.html", context)

    def __getitem__(self, item):
        return str(self)[item]


class InputLabels:
    SHUL_NAME = "Shul Name"
    ADDRESS = "Address"
    ROOM_NAME = "Room Name"
    FEMALE_LEADERSHIP = LabelWithHelpText(
        "Female Leadership",
        "Is there at least one woman in a leadership position",
    )
    CHILDCARE = LabelWithHelpText(
        "Childcare",
        "Is there an on-site childcare program",
    )
    KADDISH = LabelWithHelpText(
        "Kaddish",
        "Can women say kaddish (includes shuls where a man always says kaddish)",
    )
    WHEELCHAIR_ACCESS = LabelWithHelpText(
        "Wheelchair Access",
        "Is the women's section wheelchair accessible",
    )
    RELATIVE_SIZE = LabelWithHelpText(
        "Size of Women's Section <span class='text-nowrap'>(vs. Men's)</span>",
        "How large is the women's section relative to the men's section",
    )
    SEE_HEAR = LabelWithHelpText(
        "Audibility / Visibility",
        "How easy / difficult is it to see and hear from the women's section",
    )
    LAYOUT = LabelWithHelpText(
        "Location of Women's Section",
        "Where is the women's section located in the shul",
    )
