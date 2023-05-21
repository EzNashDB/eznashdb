import pytest
from django.urls import resolve, reverse

from eznashdb.filtersets import ShulFilterSet
from eznashdb.models import Shul


@pytest.fixture()
def test_request(rf, test_user):
    request = rf.get("/")
    request.user = test_user
    request.resolver_match = resolve(reverse("eznashdb:shuls"))
    return request


def describe_name_filter():
    @pytest.mark.parametrize(
        ("name", "query"),
        [
            ("Test Shul", "test shul"),
            ("Test Shul", "ST SH"),
            ("Test Shul", "TeSt sHuL"),
        ],
    )
    def includes_shuls_with_substring_in_name(test_user, test_request, name, query):
        Shul.objects.create(created_by=test_user, name=name)

        assert ShulFilterSet({"name": query}, request=test_request).qs.count() == 1

    def excludes_shuls_that_do_not_have_substring_in_name(test_user):
        Shul.objects.create(created_by=test_user, name="test shul")

        assert ShulFilterSet({"name": "no match"}, request=test_request).qs.count() == 0
