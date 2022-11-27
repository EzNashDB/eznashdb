from eznashdb.views import HomeView
from bs4 import BeautifulSoup
def test_shows_app_name(rf):
    request = (
        rf.get("/")
    )
    response = HomeView.as_view()(request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "Ezrat Nashim Database" in soup.get_text()