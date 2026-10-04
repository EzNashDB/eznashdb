import re
from dataclasses import dataclass
from enum import Enum

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from django.utils.translation import gettext_lazy as _

MIN_PHONE_DIGITS = 7

# Starts with an optional plus, followed by a digit or open parenthesis, followed by any number of
# valid characters. Whatever follows that run (an extension, a note, in
# any language) is free text and left alone.
_DUMB_PHONE_RE = re.compile(r"\+?[\d(][\d\s().-]*")
# The part at the end of the phone number string that can't belong to the number: everything after its last digit
# or ")".
_TRAILING_NON_NUMBER_RE = re.compile(r"[^\d)]+$")
_url_validator = URLValidator(schemes=["http", "https"])


class ContactMethod(str, Enum):
    PHONE = "phone"
    EMAIL = "email"
    URL = "url"


_ICON_CLASSES = {
    ContactMethod.PHONE: "fa-solid fa-phone",
    ContactMethod.EMAIL: "fa-solid fa-envelope",
    ContactMethod.URL: "fa-solid fa-link",
}


@dataclass(frozen=True)
class Contact:
    method: ContactMethod
    text: str  # What to display as the link text (the value as typed, minus any trailing text)
    href: str
    trailing_text: str = ""

    @property
    def icon_class(self) -> str:
        return _ICON_CLASSES[self.method]


def parse_contact(value: str) -> Contact | None:
    """
    Classify a free-form contact value, or return None if it isn't a phone number, email or URL.

    Never rewrites what the user typed - `text` and `trailing_text` are slices of the input.
    """
    value = (value or "").strip()
    if not value:
        return None
    if "@" in value:
        return _parse_email(value)
    return _parse_phone(value) or _parse_url(value)


def _parse_email(value):
    try:
        validate_email(value)
    except ValidationError:
        return None
    return Contact(ContactMethod.EMAIL, text=value, href=f"mailto:{value}")


def _parse_phone(value):
    dumb_match = _DUMB_PHONE_RE.match(value)
    if not dumb_match:
        return None
    dumb_extracted_number = dumb_match.group()
    trimmed_number = _TRAILING_NON_NUMBER_RE.sub("", dumb_extracted_number)
    digits = re.sub(r"\D", "", trimmed_number)
    if len(digits) < MIN_PHONE_DIGITS:
        return None
    plus = "+" if trimmed_number.startswith("+") else ""
    return Contact(
        ContactMethod.PHONE,
        text=trimmed_number,
        href=f"tel:{plus}{digits}",
        trailing_text=value[len(trimmed_number) :].strip(),
    )


def _parse_url(value):
    # A link needs a scheme or the browser treats it as a path on our own site, and unlike the
    # address bar it won't try variations. http:// (not https://) for a bare domain lets the
    # browser upgrade to https when it can, and follow the site's own redirect when it can't:
    # https://ketertorah.org has an expired certificate, but http://ketertorah.org redirects to
    # the working https://www.ketertorah.org.
    href = value if "://" in value else f"http://{value}"
    try:
        _url_validator(href)
    except ValidationError:
        return None
    return Contact(ContactMethod.URL, text=value, href=href)


def validate_contact(value):
    if parse_contact(value) is None:
        raise ValidationError(_("Please enter a valid website, phone number, or email"))
