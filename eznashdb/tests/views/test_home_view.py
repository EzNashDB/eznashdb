from eznashdb.views import HomeView
from bs4 import BeautifulSoup
from eznashdb.models import Shul
def test_shows_app_name(rf):
    request = (
        rf.get("/")
    )
    response = HomeView.as_view()(request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "Ezrat Nashim Database" in soup.get_text()

def test_lists_shuls(rf, test_user):
    shul = Shul.objects.create(
        created_by=test_user,
        name="test shul"
    )
    request = (
        rf.get("/")
    )
    response = HomeView.as_view()(request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert shul.name in soup.get_text()

def test_shows_message_if_no_shuls(rf):
    request = (
        rf.get("/")
    )
    response = HomeView.as_view()(request)
    soup = BeautifulSoup(str(response.render().content), features="html.parser")

    assert "No Shuls Found" in soup.get_text()