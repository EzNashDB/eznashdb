from eznashdb.views import HomeView
from bs4 import BeautifulSoup
from eznashdb.models import Shul
import pytest

@pytest.fixture()
def GET_request(GET_request_factory):
    return GET_request_factory('eznashdb:home')

def test_shows_app_name(GET_request):
    response = HomeView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "Ezrat Nashim Database" in soup.get_text()

def test_lists_shuls(GET_request, test_user):
    shul = Shul.objects.create(
        created_by=test_user,
        name="test shul"
    )

    response = HomeView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert shul.name in soup.get_text()

def test_shows_message_if_no_shuls(GET_request):
    response = HomeView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "No Shuls Found" in soup.get_text()
