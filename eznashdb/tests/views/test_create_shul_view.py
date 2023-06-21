import pytest
from bs4 import BeautifulSoup

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
