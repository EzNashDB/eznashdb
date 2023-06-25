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
            "name": "test shul",
            "has_female_leadership": True,
            "has_childcare": True,
            "can_say_kaddish": True,
        },
    )
    assert Shul.objects.count() == 1


def test_redirects_to_shuls_list_view(client):
    response = client.post(
        reverse("eznashdb:create_shul"),
        data={
            "name": "test shul",
            "has_female_leadership": True,
            "has_childcare": True,
            "can_say_kaddish": True,
        },
        follow=True,
    )
    assert response.resolver_match.view_name == "eznashdb:shuls"
