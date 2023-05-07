from django.db import models
from django.utils.translation import gettext_lazy as _


class RelativeSize(models.TextChoices):
    XS = ("XS", _("Much smaller"))
    S = ("S", _("Smaller"))
    M = ("M", _("Same size"))
    L = ("L", _("Larger"))


class SeeHearScore(models.IntegerChoices):
    _1_VERY_DIFFICULT = 1
    _2_DIFFICULT = 2
    _3_AVERAGE = 3
    _4_EASY = 4
    _5_VERY_EASY = 5
