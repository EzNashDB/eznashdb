"""Client for Brevo (user-facing broadcast email), separate from the admin
email sent via app/emails.py. Syncing a contact is best-effort: a Brevo outage
or misconfiguration must never break user signup, so every call here is
guarded and swallows its own errors.
"""

import logging

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()

BREVO_API_BASE = "https://api.brevo.com/v3"
REQUEST_TIMEOUT_SECONDS = 5


def is_enabled():
    return bool(settings.BREVO_API_KEY)


def _post(path, payload):
    """POST to the Brevo API. Returns the response, or None on failure/disabled."""
    if not is_enabled():
        return None

    try:
        response = requests.post(
            f"{BREVO_API_BASE}{path}",
            json=payload,
            headers={
                "api-key": settings.BREVO_API_KEY,
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logger.warning(f"Brevo request to {path} failed: {e}")
        return None


def sync_contact(user):
    """
    Upsert a user as a Brevo contact on the broadcast list.

    Safe to call repeatedly (e.g. before every campaign): Brevo's updateEnabled
    upsert does not resubscribe a contact who has since unsubscribed.
    """
    if not user.email:
        return None

    payload = {
        "email": user.email,
        "attributes": {
            "FIRSTNAME": user.first_name,
            "LASTNAME": user.last_name,
        },
        "listIds": [int(settings.BREVO_CONTACT_LIST_ID)] if settings.BREVO_CONTACT_LIST_ID else [],
        "updateEnabled": True,
    }
    response = _post("/contacts", payload)
    if response is not None:
        User.objects.filter(pk=user.pk).update(brevo_synced_at=timezone.now())
    return response
