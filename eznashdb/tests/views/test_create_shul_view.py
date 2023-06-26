import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from eznashdb.models import Shul
from eznashdb.views import CreateShulView


@pytest.fixture()
def GET_request(rf_GET):
    return rf_GET("eznashdb:create_shul")


def test_shows_page_title(GET_request):
    response = CreateShulView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "add a shul" in soup.get_text().lower()


def test_shows_form(GET_request):
    response = CreateShulView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert soup.find("form")


def test_creates_a_shul(client):
    client.post(
        reverse("eznashdb:create_shul"),
        data={
            "can_say_kaddish": "unknown",
            "has_childcare": "unknown",
            "has_female_leadership": "unknown",
            "name": "test shul",
            "rooms-0-id": "",
            "rooms-0-name": "",
            "rooms-0-shul": "",
            "rooms-INITIAL_FORMS": "0",
            "rooms-MAX_NUM_FORMS": "1000",
            "rooms-MIN_NUM_FORMS": "0",
            "rooms-TOTAL_FORMS": "1",
        },
    )
    assert Shul.objects.count() == 1


def test_creates_a_room(client):
    client.post(
        reverse("eznashdb:create_shul"),
        data={
            "can_say_kaddish": "unknown",
            "has_childcare": "unknown",
            "has_female_leadership": "unknown",
            "name": "test shul",
            "rooms-0-id": "",
            "rooms-0-name": "test room",
            "rooms-0-shul": "",
            "rooms-INITIAL_FORMS": "0",
            "rooms-MAX_NUM_FORMS": "1000",
            "rooms-MIN_NUM_FORMS": "0",
            "rooms-TOTAL_FORMS": "1",
        },
    )
    assert Shul.objects.first().rooms.count() == 1


def test_creates_multiple_rooms(client):
    client.post(
        reverse("eznashdb:create_shul"),
        data={
            "can_say_kaddish": "unknown",
            "has_childcare": "unknown",
            "has_female_leadership": "unknown",
            "name": "test shul",
            "rooms-0-id": "",
            "rooms-0-name": "test room 1",
            "rooms-0-shul": "",
            "rooms-1-id": "",
            "rooms-1-name": "test room 2",
            "rooms-1-shul": "",
            "rooms-INITIAL_FORMS": "0",
            "rooms-MAX_NUM_FORMS": "1000",
            "rooms-MIN_NUM_FORMS": "0",
            "rooms-TOTAL_FORMS": "2",
        },
    )
    assert Shul.objects.first().rooms.count() == 2


def test_redirects_to_shuls_list_view(client):
    response = client.post(
        reverse("eznashdb:create_shul"),
        data={
            "can_say_kaddish": "unknown",
            "has_childcare": "unknown",
            "has_female_leadership": "unknown",
            "name": "test shul",
            "rooms-0-id": "",
            "rooms-0-name": "",
            "rooms-0-shul": "",
            "rooms-INITIAL_FORMS": "0",
            "rooms-MAX_NUM_FORMS": "1000",
            "rooms-MIN_NUM_FORMS": "0",
            "rooms-TOTAL_FORMS": "1",
        },
        follow=True,
    )
    assert response.resolver_match.view_name == "eznashdb:shuls"
