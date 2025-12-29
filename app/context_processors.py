from dataclasses import dataclass

from django.urls import reverse


@dataclass
class NavbarItem:
    label: str
    url: str
    is_active: bool = False


def navbar(request):
    # Define your navbar items here
    navbar_items = [
        NavbarItem("Browse Shuls", reverse("eznashdb:shuls")),
        NavbarItem("Add a Shul", reverse("eznashdb:create_shul")),
        NavbarItem("About", "/about/"),
        NavbarItem("Contact", reverse("eznashdb:contact_us")),
    ]

    # Authentication links - dropdown for authenticated users handled in template
    if not (hasattr(request, "user") and request.user.is_authenticated):
        navbar_items.append(NavbarItem("Login", reverse("account_login")))
        navbar_items.append(NavbarItem("Sign Up", reverse("account_signup")))

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
