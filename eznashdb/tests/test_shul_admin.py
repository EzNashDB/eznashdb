from django.contrib import admin
from django.utils.html import strip_tags

from eznashdb.models import Shul


def describe_shul_admin():
    def _shul_admin():
        return admin.site._registry[Shul]

    def escapes_html_in_room_names(test_shul):
        test_shul.rooms.create(name="<img src=x onerror=alert(1)>")

        html = _shul_admin().rooms_links(test_shul)

        assert "<img" not in html
        assert "&lt;img" in html

    def shortens_a_long_contact_but_keeps_the_full_value_on_hover(test_shul):
        test_shul.contact = "https://www.totallyjewishtravel.com/some/long/path"

        html = _shul_admin().short_contact(test_shul)

        assert len(strip_tags(html)) < len(test_shul.contact)
        assert f'title="{test_shul.contact}"' in html

    def shows_a_dash_when_there_is_no_contact(test_shul):
        assert _shul_admin().short_contact(test_shul) == "-"
