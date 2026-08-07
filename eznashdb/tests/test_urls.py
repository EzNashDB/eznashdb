import pytest
from django.urls import resolve, reverse

from eznashdb.views import (
    AddressLookupView,
    CreateUpdateShulView,
    ShulClusterPopupView,
    ShulsFilterView,
)


@pytest.mark.parametrize(
    ("view_name", "view", "args", "kwargs"),
    [
        ("eznashdb:shuls", ShulsFilterView, [], {}),
        ("eznashdb:cluster_popup", ShulClusterPopupView, [], {}),
        ("eznashdb:create_shul", CreateUpdateShulView, [], {}),
        ("eznashdb:update_shul", CreateUpdateShulView, [], {"pk": 1}),
        ("eznashdb:address_lookup", AddressLookupView, [], {}),
    ],
)
def test_urls_with_class_based_views(view_name, view, args, kwargs):
    url = reverse(view_name, args=args or None, kwargs=kwargs or None)
    assert resolve(url).func.view_class == view
