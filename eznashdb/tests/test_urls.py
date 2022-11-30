import pytest
from django.urls import resolve, reverse

from eznashdb.views import HomeView


@pytest.mark.parametrize(
    "view_name,view,args",
    [
        ("eznashdb:home", HomeView, []),
    ],
)
def test_urls_with_class_based_views(view_name, view, args):
    url = reverse(view_name, args=(args if args else None))
    assert resolve(url).func.view_class == view
