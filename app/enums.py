"""Enums and choices for the app."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class RateLimitedEndpoint(models.TextChoices):
    """Rate-limited endpoints."""

    COORDINATE_ACCESS = "COORDINATE_ACCESS", _("Coordinate Access")
