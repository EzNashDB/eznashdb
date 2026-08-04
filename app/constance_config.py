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
        "120/60m",
        "Rate string, e.g. '120/60m' = 120 budget units per 60 minutes "
        "(see URL_ABUSE_POINTS in app/abuse_prevention.py for unit cost per endpoint)",
    ),
    Entry("ABUSE_EPISODE_INACTIVITY_MINUTES", 60, "Minutes of inactivity before an abuse episode ends"),
    Entry(
        "ABUSE_POINTS_CAP_PER_EPISODE",
        40,
        "Max budget units allowed per episode before blocking",
    ),
    Entry("ABUSE_STRIKES_DECAY_HOURS", 24, "Hours between each automatic 1-strike decay"),
    Entry("ABUSE_PERMANENT_BAN_THRESHOLD", 5, "Strikes at which a user is permanently banned"),
    Entry("ABUSE_CAPTCHA_THRESHOLD", 1, "Minimum strikes at which CAPTCHA is required"),
    Entry(
        "ABUSE_COOLDOWN_LADDER",
        [0, 0, 60, 120, 1440],
        "Cooldown minutes per abuse score (index = strikes)",
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
        "ABUSE_POINTS_CAP_PER_EPISODE",
        "ABUSE_STRIKES_DECAY_HOURS",
        "ABUSE_PERMANENT_BAN_THRESHOLD",
        "ABUSE_CAPTCHA_THRESHOLD",
        "ABUSE_COOLDOWN_LADDER",
    ],
}
