from django.db import models
from django.utils.translation import gettext_lazy as _


class RelativeSize(models.TextChoices):
    XS = ("XS", _("Much smaller"))
    S = ("S", _("Smaller"))
    M = ("M", _("Same size"))
    L = ("L", _("Larger"))


class SeeHearScore(models.TextChoices):
    _1 = ("1", _("Very difficult"))
    _2 = ("2", _("Difficult"))
    _3 = ("3", _("Moderate"))
    _4 = ("4", _("Easy"))
    _5 = ("5", _("Very easy"))
