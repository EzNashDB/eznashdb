from collections import namedtuple


def navbar(request):
    NavbarItem = namedtuple("NavbarItem", "label view_name")
    current_app_name = request.resolver_match.app_names[0]
    current_url_name = request.resolver_match.url_name
    return {
        "current_view_name": f"{current_app_name}:{current_url_name}",
        "navbar_items": [
            NavbarItem("Search Shuls", "eznashdb:shuls"),
            NavbarItem("Add a Shul", "eznashdb:create_shul"),
            NavbarItem("Contact Us", "eznashdb:contact_us"),
        ],
    }
