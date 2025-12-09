from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

BLANK_CHOICE = ("", "-------")


def get_size_option_display(letter, explanation):
    return f"""
        <div class='d-inline-flex gap-1'>
            <div>
                <kbd class='fw-bold'>{letter}</kbd>
            </div>
            -
            <div class='flex-grow-1 overflow-hidden text-break'>
                {explanation}
            </div>
        </div>
    """


class RelativeSize(models.TextChoices):
    L = "L", _("Equal or larger than men's")
    M = "M", _("At least half men's size")
    S = "S", _("Less than half men's size")
    X = "X", _("No women's section")
    MIXED = "&", _("Mixed seating")

    def get_display(self):
        return mark_safe(get_size_option_display(self.value, self.label))

    @classmethod
    def get_display_choices(cls, include_blank=False):
        choices = [(c.value, c.get_display()) for c in cls]
        if include_blank:
            choices = [BLANK_CHOICE] + choices
        return choices


def get_star_display(score):
    divs = []
    for i in range(5):
        if i < score:
            divs.append("<i class='fa-solid fa-star text-warning'></i>")
        else:
            divs.append("<i class='fa-regular fa-star text-warning'></i>")
    stars = "".join(divs)
    return f"<span class='text-nowrap'><kbd class='fw-bold'>{score}</kbd> - {stars}</span>"


class SeeHearScore(models.TextChoices):
    _5 = "5"
    _4 = "4"
    _3 = "3"
    _2 = "2"
    _1 = "1"

    def get_display(self):
        return mark_safe(get_star_display(int(self)))

    @classmethod
    def get_display_choices(cls, include_blank=False):
        choices = [(c.value, c.get_display()) for c in cls]
        if include_blank:
            choices = [BLANK_CHOICE] + choices
        return choices
