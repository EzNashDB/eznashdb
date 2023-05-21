import pytest
from bs4 import BeautifulSoup

from eznashdb.views import CreateUpdateShulView


@pytest.fixture()
def GET_request(GET_request_factory):
    return GET_request_factory('eznashdb:create_shul')

def test_shows_page_title(GET_request):
    response = CreateUpdateShulView.as_view()(GET_request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "add a shul" in soup.get_text().lower()
