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

    # Mark which item is active
    current_path = request.path
    for item in navbar_items:
        item.is_active = item.url == current_path

    return {
        "navbar_items": navbar_items,
    }
