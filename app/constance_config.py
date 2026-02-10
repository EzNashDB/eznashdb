from typing import Any, NamedTuple


class Entry(NamedTuple):
    key: str
    value: Any
    help_text: str = ""


ENTRIES = [
    Entry("GOOGLE_PLACES_MONTHLY_AUTOCOMPLETE_LIMIT", 10000),
    Entry("GOOGLE_PLACES_MONTHLY_DETAILS_LIMIT", 10000),
]
CONSTANCE_CONFIG = {entry.key: (entry.value, entry.help_text) for entry in ENTRIES}
