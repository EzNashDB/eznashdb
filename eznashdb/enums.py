from django.db import models
from django.utils.translation import gettext_lazy as _


class RelativeSize(models.TextChoices):
    S = ("S", _("S: Less than half of men's"))
    M = ("M", _("M: Smaller than men's, but at least half"))
    L = ("L", _("L: Same size as men's or larger"))


class SeeHearScore(models.TextChoices):
    _5 = ("5", _("5: Equal to men's"))
    _4 = ("4", _("4"))
    _3 = ("3", _("3"))
    _2 = ("2", _("2"))
    _1 = ("1", _("1: Much more difficult"))
