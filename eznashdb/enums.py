from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


def get_size_option_display(letter, explanation):
    return f"<span class='text-nowrap'><kbd class='fw-bold'>{letter}</kbd><small> - {explanation}</small></span>"


class RelativeSize(models.TextChoices):
    L = "L", _(get_size_option_display("L", "Equal or larger than men's"))
    M = "M", _(get_size_option_display("M", "At least half men's size"))
    S = "S", _(get_size_option_display("S", "Less than half men's size"))
    X = "X", _(get_size_option_display("X", "No women's section"))
    MIXED = "&", _(get_size_option_display("&", "Mixed seating"))


def get_star_display(score):
    divs = []
    for i in range(5):
        if i < score:
            divs.append("<i class='fa-solid fa-star text-warning'></i>")
        else:
            divs.append("<i class='fa-regular fa-star text-warning'></i>")
    stars = "".join(divs)
    return (
        f"<span class='text-nowrap'><kbd class='fw-bold'>{score}</kbd> <small> - {stars}</small></span>"
    )


class SeeHearScore(models.TextChoices):
    _5 = "5", _(mark_safe(get_star_display(5)))
    _4 = "4", _(mark_safe(get_star_display(4)))
    _3 = "3", _(mark_safe(get_star_display(3)))
    _2 = "2", _(mark_safe(get_star_display(2)))
    _1 = "1", _(mark_safe(get_star_display(1)))
