from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class RelativeSize(models.TextChoices):
    S = ("S", _("S: Less than half of men's"))
    M = ("M", _("M: Smaller than men's, but at least half"))
    L = ("L", _("L: Same size as men's or larger"))


def get_star_display(score):
    divs = []
    for i in range(5):
        if i < score:
            divs.append("<i class='fa-solid fa-star text-warning'></i>")
        else:
            divs.append("<i class='fa-regular fa-star text-warning'></i>")
    stars = "".join(divs)
    return f"<small>{stars} ({score})</small>"


class SeeHearScore(models.TextChoices):
    _5 = "5", _(mark_safe(get_star_display(5)))
    _4 = "4", _(mark_safe(get_star_display(4)))
    _3 = "3", _(mark_safe(get_star_display(3)))
    _2 = "2", _(mark_safe(get_star_display(2)))
    _1 = "1", _(mark_safe(get_star_display(1)))
