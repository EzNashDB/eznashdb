from django.contrib import admin

from eznashdb.models import Shul


def test_shul_admin_escapes_html_in_room_names(test_shul):
    test_shul.rooms.create(name="<img src=x onerror=alert(1)>")

    html = admin.site._registry[Shul].rooms_links(test_shul)

    assert "<img" not in html
    assert "&lt;img" in html
