from eznashdb.views import CreateUpdateShulView
from bs4 import BeautifulSoup
from eznashdb.models import Shul

def test_shows_page_title(rf):
    request = (
        rf.get("/")
    )
    response = CreateUpdateShulView.as_view()(request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "add a shul" in soup.get_text().lower()

