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


def describe_shul_name():
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


def describe_has_female_leadership():
    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, "True"),
            (False, "False"),
            (None, "--"),
        ],
    )
    def includes_shuls_that_match_single_value(test_user, test_request, value, query):
        Shul.objects.create(created_by=test_user, has_female_leadership=value)

        assert ShulFilterSet({"has_female_leadership": [query]}, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, ["True", "False"]),
            (False, ["False", "--"]),
            (None, ["True", "--"]),
        ],
    )
    def includes_shuls_that_match_any_of_multiple_values(test_user, test_request, value, query):
        Shul.objects.create(created_by=test_user, has_female_leadership=value)

        assert ShulFilterSet({"has_female_leadership": [query]}, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, ["False", "--"]),
            (False, ["True", "--"]),
            (None, ["True", "False"]),
        ],
    )
    def excludes_shuls_that_do_not_match_any_of_value(test_user, test_request, value, query):
        Shul.objects.create(created_by=test_user, has_female_leadership=value)

        assert ShulFilterSet({"has_female_leadership": [query]}, request=test_request).qs.count() == 1


def describe_has_childcare():
    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, "True"),
            (False, "False"),
            (None, "--"),
        ],
    )
    def includes_shuls_that_match_single_value(test_user, test_request, value, query):
        Shul.objects.create(created_by=test_user, has_childcare=value)

        assert ShulFilterSet({"has_childcare": [query]}, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, ["True", "False"]),
            (False, ["False", "--"]),
            (None, ["True", "--"]),
        ],
    )
    def includes_shuls_that_match_any_of_multiple_values(test_user, test_request, value, query):
        Shul.objects.create(created_by=test_user, has_childcare=value)

        assert ShulFilterSet({"has_childcare": [query]}, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, ["False", "--"]),
            (False, ["True", "--"]),
            (None, ["True", "False"]),
        ],
    )
    def excludes_shuls_that_do_not_match_any_of_value(test_user, test_request, value, query):
        Shul.objects.create(created_by=test_user, has_childcare=value)

        assert ShulFilterSet({"has_childcare": [query]}, request=test_request).qs.count() == 1
