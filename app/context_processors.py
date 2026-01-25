from dataclasses import dataclass

from django.conf import settings
from django.urls import reverse

from app.fields import HONEYPOT_FIELD_CLASS


@dataclass
class NavbarItem:
    label: str
    url: str
    is_active: bool = False


def _get_login_url(request):
    """Return appropriate login URL based on environment and host."""
    google_login = "/accounts/google/login/"
    if not settings.DEBUG:
        return google_login
    # In DEBUG, use Google for localhost, fallback page for other hosts (e.g. local IP)
    host = request.get_host().split(":")[0]
    if host == "localhost":
        return google_login
    return "/accounts/login/"


def navbar(request):
    # Define your navbar items here
    navbar_items = [
        NavbarItem("Browse", reverse("eznashdb:shuls")),
        NavbarItem("Add a Shul", reverse("eznashdb:create_shul")),
        NavbarItem("About", "/about/"),
        NavbarItem("Contact", reverse("eznashdb:contact_us")),
    ]

    # Authentication links - dropdown for authenticated users handled in template
    if not (hasattr(request, "user") and request.user.is_authenticated):
        navbar_items.append(NavbarItem("Sign in", _get_login_url(request)))

    # Add admin link for staff users
    if hasattr(request, "user") and request.user.is_staff:
        navbar_items.append(NavbarItem("Admin", reverse("admin_dashboard")))

    # Mark which item is active
    current_path = request.path
    for item in navbar_items:
        item.is_active = item.url == current_path

    return {
        "navbar_items": navbar_items,
    }


def honeypot(request):
    return {
        "HONEYPOT_FIELD_CLASS": HONEYPOT_FIELD_CLASS,
    }
