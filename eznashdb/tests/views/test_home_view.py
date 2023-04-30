from eznashdb.views import HomeView
from bs4 import BeautifulSoup
from eznashdb.models import Shul
import pytest


@pytest.fixture()
def GET_request(GET_request_factory):
    return GET_request_factory("eznashdb:home")


def test_shows_app_name(GET_request):
    response = HomeView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "Ezrat Nashim Database" in soup.get_text()


def test_shows_shul_name(GET_request, test_user):
    shul = Shul.objects.create(created_by=test_user, name="test shul")

    response = HomeView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert shul.name in soup.get_text()


@pytest.mark.parametrize(
    ("field_name", "field_value", "display_value"),
    [
        ("has_female_leadership", True, "fa-check"),
        ("has_female_leadership", False, "fa-times"),
        ("has_childcare", True, "fa-check"),
        ("has_childcare", False, "fa-times"),
        ("can_say_kaddish", True, "fa-check"),
        ("can_say_kaddish", False, "fa-times"),
    ],
)
def test_shows_shul_details(
    GET_request, test_user, field_name, field_value, display_value
):
    Shul.objects.create(
        created_by=test_user, name="test shul", **{field_name: field_value}
    )

    response = HomeView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert display_value in str(soup)


def test_shows_message_if_no_shuls(GET_request):
    response = HomeView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "No Shuls Found" in soup.get_text()
