from typing import Any, NamedTuple


class Entry(NamedTuple):
    key: str
    value: Any
    help_text: str = ""
    field_type: type | None = None


ENTRIES = [
    # Google Places API
    Entry("GOOGLE_PLACES_MONTHLY_AUTOCOMPLETE_LIMIT", 10000),
    Entry("GOOGLE_PLACES_MONTHLY_DETAILS_LIMIT", 10000),
    # Abuse Prevention
    Entry(
        "ABUSE_RATE_LIMIT",
        "30/60m",
        "django-ratelimit rate string, e.g. '30/60m' = 30 requests per 60 minutes",
    ),
    Entry("ABUSE_EPISODE_INACTIVITY_MINUTES", 60, "Minutes of inactivity before an abuse episode ends"),
    Entry(
        "ABUSE_SENSITIVE_CAP_PER_EPISODE",
        10,
        "Max sensitive requests allowed per episode before blocking",
    ),
    Entry("ABUSE_POINTS_DECAY_HOURS", 24, "Hours between each automatic 1-point decay"),
    Entry("ABUSE_PERMANENT_BAN_THRESHOLD", 5, "Points at which a user is permanently banned"),
    Entry("ABUSE_CAPTCHA_THRESHOLD", 1, "Minimum points at which CAPTCHA is required"),
    Entry(
        "ABUSE_COOLDOWN_LADDER",
        [0, 0, 60, 120, 1440],
        "Cooldown minutes per abuse score (index = points)",
        list,
    ),
]

CONSTANCE_ADDITIONAL_FIELDS = {
    list: ["django.forms.fields.JSONField", {"widget": "django.forms.Textarea"}],
}

CONSTANCE_CONFIG = {
    entry.key: (entry.value, entry.help_text, entry.field_type)
    if entry.field_type
    else (entry.value, entry.help_text)
    for entry in ENTRIES
}

CONSTANCE_CONFIG_FIELDSETS = {
    "Google Places API": [
        "GOOGLE_PLACES_MONTHLY_AUTOCOMPLETE_LIMIT",
        "GOOGLE_PLACES_MONTHLY_DETAILS_LIMIT",
    ],
    "Abuse Prevention": [
        "ABUSE_RATE_LIMIT",
        "ABUSE_EPISODE_INACTIVITY_MINUTES",
        "ABUSE_SENSITIVE_CAP_PER_EPISODE",
        "ABUSE_POINTS_DECAY_HOURS",
        "ABUSE_PERMANENT_BAN_THRESHOLD",
        "ABUSE_CAPTCHA_THRESHOLD",
        "ABUSE_COOLDOWN_LADDER",
    ],
}
