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


class YesNoUnknownFilterTest:
    shul_model_field = None

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, "True"),
            (False, "False"),
            (None, "--"),
        ],
    )
    @pytest.mark.usefixtures("test_user", "test_request", "value", "query")
    def test_includes_shuls_that_match_single_value(self, test_user, test_request, value, query):
        Shul.objects.create(created_by=test_user, **{self.shul_model_field: value})

        assert ShulFilterSet({self.shul_model_field: [query]}, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, ["True", "False"]),
            (False, ["False", "--"]),
            (None, ["True", "--"]),
        ],
    )
    def test_includes_shuls_that_match_any_of_multiple_values(
        self, test_user, test_request, value, query
    ):
        Shul.objects.create(created_by=test_user, **{self.shul_model_field: value})

        assert ShulFilterSet({self.shul_model_field: [query]}, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, ["False", "--"]),
            (False, ["True", "--"]),
            (None, ["True", "False"]),
        ],
    )
    def test_excludes_shuls_that_do_not_match_any_value(self, test_user, test_request, value, query):
        Shul.objects.create(created_by=test_user, **{self.shul_model_field: value})

        assert ShulFilterSet({self.shul_model_field: [query]}, request=test_request).qs.count() == 1


class TestFemaleLeadershipFilter(YesNoUnknownFilterTest):
    shul_model_field = "has_female_leadership"


class TestChildcareFilter(YesNoUnknownFilterTest):
    shul_model_field = "has_childcare"