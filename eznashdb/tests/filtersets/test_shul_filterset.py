import pytest
from django.urls import resolve, reverse

from eznashdb.enums import RelativeSize, SeeHearScore
from eznashdb.filtersets import ShulFilterSet
from eznashdb.models import Shul


@pytest.fixture
def test_request(rf, test_user):
    request = rf.get("/")
    request.user = test_user
    request.resolver_match = resolve(reverse("eznashdb:shuls"))
    return request


class YesNoUnknownFilterTest:
    shul_model_field = None

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, ["True"]),
            (False, ["False"]),
            (None, ["--"]),
        ],
    )
    def test_includes_shuls_that_match_single_value(self, test_shul, test_request, value, query):
        Shul.objects.filter(pk=test_shul.pk).update(**{self.shul_model_field: value})
        assert ShulFilterSet({self.shul_model_field: query}, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, ["True", "False"]),
            (False, ["False", "--"]),
            (None, ["True", "--"]),
        ],
    )
    def test_includes_shuls_that_match_any_of_multiple_values(
        self, test_shul, test_request, value, query
    ):
        Shul.objects.filter(pk=test_shul.pk).update(**{self.shul_model_field: value})

        assert ShulFilterSet({self.shul_model_field: query}, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, ["False", "--"]),
            (False, ["True", "--"]),
            (None, ["True", "False"]),
        ],
    )
    def test_excludes_shuls_that_do_not_match_any_value(self, test_request, test_shul, value, query):
        Shul.objects.filter(pk=test_shul.pk).update(**{self.shul_model_field: value})

        assert ShulFilterSet({self.shul_model_field: query}, request=test_request).qs.count() == 0


def describe_relative_size_filter():
    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (RelativeSize.S.value, ["S"]),
            (RelativeSize.M.value, ["M"]),
            (RelativeSize.L.value, ["L"]),
            ("", ["--"]),
        ],
    )
    def includes_shuls_that_match_single_value(test_request, test_shul, value, query):
        test_shul.rooms.create(relative_size=value)

        data = {"rooms__relative_size": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    def shul_appears_once_if_multiple_rooms_match(test_shul, test_request):
        test_shul.rooms.create(relative_size=RelativeSize.M.value)
        test_shul.rooms.create(relative_size=RelativeSize.M.value)

        data = {"rooms__relative_size": ["M"]}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            # (RelativeSize.M.value, ["M", "L"]),
            (RelativeSize.M.value, ["M", "--"]),
            ("", ["M", "--"]),
        ],
    )
    def includes_shuls_that_match_any_of_multiple_values(test_request, test_shul, value, query):
        test_shul.rooms.create(relative_size=value)

        data = {"rooms__relative_size": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (RelativeSize.M.value, ["L", "S"]),
            ("", ["S", "M"]),
        ],
    )
    def excludes_shuls_that_do_not_match_any_value(test_shul, test_request, value, query):
        test_shul.rooms.create(relative_size=value)

        data = {"rooms__relative_size": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 0

    def unknown_includes_shuls_without_rooms(test_request, test_shul):
        data = {"rooms__relative_size": ["--"]}
        assert test_shul in ShulFilterSet(data, request=test_request).qs


def describe_see_hear_score_filter():
    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (SeeHearScore._1.value, ["1"]),
            (SeeHearScore._2.value, ["2"]),
            (SeeHearScore._3.value, ["3"]),
            (SeeHearScore._4.value, ["4"]),
            (SeeHearScore._5.value, ["5"]),
            ("", ["--"]),
        ],
    )
    def includes_shuls_that_match_single_value(test_shul, test_request, value, query):
        test_shul.rooms.create(see_hear_score=value)

        data = {"rooms__see_hear_score": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    def shul_appears_once_if_multiple_rooms_match(test_shul, test_request):
        test_shul.rooms.create(see_hear_score=SeeHearScore._3.value)
        test_shul.rooms.create(see_hear_score=SeeHearScore._3.value)

        data = {"rooms__see_hear_score": ["M"]}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (SeeHearScore._3.value, ["3", "5"]),
            (SeeHearScore._3.value, ["3", "--"]),
            ("", ["4", "--"]),
        ],
    )
    def includes_shuls_that_match_any_of_multiple_values(test_shul, test_request, value, query):
        test_shul.rooms.create(see_hear_score=value)

        data = {"rooms__see_hear_score": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (SeeHearScore._3.value, ["4", "5"]),
            ("", ["4", "3"]),
        ],
    )
    def excludes_shuls_that_do_not_match_any_value(test_shul, test_request, value, query):
        test_shul.rooms.create(see_hear_score=value)

        data = {"rooms__see_hear_score": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 0

    def unknown_includes_shuls_without_rooms(test_shul, test_request):
        data = {"rooms__see_hear_score": ["--"]}
        assert test_shul in ShulFilterSet(data, request=test_request).qs


def describe_name_filter():
    def includes_shul_with_matching_name(test_shul, test_request):
        data = {"name": [test_shul.name]}
        assert test_shul in ShulFilterSet(data, request=test_request).qs

    def includes_shuls_matching_any_of_multiple_names(test_shul, test_request):
        other_shul = Shul.objects.create(name="Another Shul", latitude=0, longitude=0)
        data = {"name": [test_shul.name, other_shul.name]}
        qs = ShulFilterSet(data, request=test_request).qs
        assert test_shul in qs
        assert other_shul in qs

    def excludes_shuls_that_do_not_match(test_shul, test_request):
        other_shul = Shul.objects.create(name="Another Shul", latitude=0, longitude=0)
        data = {"name": [other_shul.name]}
        assert test_shul not in ShulFilterSet(data, request=test_request).qs

    def returns_all_shuls_when_empty(test_shul, test_request):
        data = {"name": []}
        assert test_shul in ShulFilterSet(data, request=test_request).qs
