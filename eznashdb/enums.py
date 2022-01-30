from django.db import models
from django.utils.translation import gettext_lazy as _

class KaddishAlone(models.TextChoices):
    YES = ("YES", _("Yes"))
    NO = ("NO", _("No"))
    MAN_ALWAYS_SAYS_KADDISH = ("MAN_ALWAYS_SAYS_KADDISH", _("Man always says kaddish"))

class RelativeSize(models.TextChoices):
    MUCH_SMALLER = ("MUCH_SMALLER", _("Much smaller"))
    SOMEWHAT_SMALLER = ("SOMEWHAT_SMALLER", _("Somewhat smaller"))
    SAME_SIZE = ("SAME_SIZE", _("Same size"))
    LARGER = ("LARGER", _("Larger"))

class SeeHearScore(models.IntegerChoices):
    _1_VERY_DIFFICULT = 1
    _2_DIFFICULT = 2
    _3_AVERAGE = 3
    _4_EASY = 4
    _5_VERY_EASY = 5
