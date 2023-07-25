import pytest
from django.urls import resolve, reverse

from eznashdb.views import CityLookupView, CreateShulView, DeleteShulView, ShulsFilterView


@pytest.mark.parametrize(
    ("view_name", "view", "args", "kwargs"),
    [
        ("eznashdb:shuls", ShulsFilterView, [], {}),
        ("eznashdb:create_shul", CreateShulView, [], {}),
        ("eznashdb:delete_shul", DeleteShulView, [], {"pk": 1}),
        ("eznashdb:city_lookup", CityLookupView, [], {}),
    ],
)
def test_urls_with_class_based_views(view_name, view, args, kwargs):
    url = reverse(view_name, args=args or None, kwargs=kwargs or None)
    assert resolve(url).func.view_class == view
