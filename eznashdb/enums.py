from enum import Enum

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class GeocodingProvider(str, Enum):
    """Provider for geocoding/place search services."""

    GOOGLE = "google"
    OSM = "osm"


class DisplayChoicesMixin:
    """Mixin to provide custom display choices for TextChoices enums."""

    def get_display(self):
        """Override in subclass to provide custom display HTML."""
        raise NotImplementedError

    @classmethod
    def get_display_choices(cls, include_blank=False):
        """Generate choices with custom display HTML."""
        choices = [(choice.value, choice.get_option_display()) for choice in cls]
        if include_blank:
            choices = [("", "-------")] + choices
        return choices


class RelativeSize(DisplayChoicesMixin, models.TextChoices):
    L = "L", _("Equal or larger than men's")
    M = "M", _("At least half men's size")
    S = "S", _("Less than half men's size")
    X = "X", _("No women's section")
    MIXED = "&", _("Mixed seating")

    def get_display(self):
        return mark_safe(
            f"""
            <div class='text-wrap-pretty'>
                <span class='flex-grow-1 overflow-hidden text-break'>
                {self.label}
                </span>
            </div>
            """
        )

    def get_option_display(self):
        return mark_safe(
            f"""
            <div class='d-flex align-items-center gap-2'>
                <span class='badge text-bg-secondary px-1 d-inline-block text-center' style='width: 1.5rem;'>{self.value}</span> {self.label}
            </div>
            """
        )


class SeeHearScore(DisplayChoicesMixin, models.TextChoices):
    _5 = "5"
    _4 = "4"
    _3 = "3"
    _2 = "2"
    _1 = "1"

    def get_display(self):
        score = int(self.value)
        stars = self._render_stars(score)
        return mark_safe(f"<span class='text-nowrap'>{stars}</span>")

    def get_option_display(self):
        score = int(self.value)
        stars = self._render_stars(score)
        return mark_safe(
            f"""
            <span>
                <span class='badge bg-secondary me-1 d-inline-block text-center' style='width: 1.5rem;'>{self.value}</span>
                <span class='text-nowrap'>{stars}</span>
            </span>
            """
        )

    @staticmethod
    def _render_stars(score):
        """Render star icons based on score."""
        filled = "<i class='fa-solid fa-star text-warning'></i>"
        empty = "<i class='fa-regular fa-star text-warning'></i>"
        return "".join(filled if i < score else empty for i in range(5))


class IconDisplayChoicesMixin(DisplayChoicesMixin):
    """DisplayChoicesMixin that renders a leading FontAwesome icon."""

    @property
    def icon_class(self):
        raise NotImplementedError

    def get_display(self):
        return mark_safe(f"<i class='{self.icon_class}'></i> {self.label}")

    def get_option_display(self):
        return mark_safe(
            f"""
            <div class='d-flex align-items-center gap-2'>
                <i class='{self.icon_class}'></i> {self.label}
            </div>
            """
        )


class KaddishPolicy(IconDisplayChoicesMixin, models.TextChoices):
    CAN_SAY_ALONE = "CAN_SAY_ALONE", _("Can say alone")
    SHUL_ENSURES_MAN = "SHUL_ENSURES_MAN", _("Shul ensures a man will join")
    ONLY_IF_MAN = "ONLY_IF_MAN", _("Only with men, need to coordinate")
    NO = "NO", _("Not allowed")

    @property
    def icon_class(self):
        return {
            self.CAN_SAY_ALONE: "fa-solid fa-circle-check text-success",
            self.SHUL_ENSURES_MAN: "fa-solid fa-circle-check text-success",
            self.ONLY_IF_MAN: "fa-solid fa-circle-exclamation text-warning",
            self.NO: "fa-solid fa-circle-xmark text-danger",
        }[self]
