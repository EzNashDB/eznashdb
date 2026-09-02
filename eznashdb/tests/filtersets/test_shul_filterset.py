import pytest
from django.urls import resolve, reverse
from django.utils import translation

from eznashdb.enums import KaddishPolicy, RelativeSize, SeeHearScore
from eznashdb.filtersets import ShulFilterSet
from eznashdb.models import Shul


@pytest.fixture
def test_request(rf, test_user):
    request = rf.get("/")
    request.user = test_user
    request.resolver_match = resolve(reverse("eznashdb:shuls"))
    return request


def describe_relative_size_filter():
    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (RelativeSize.S.value, ["S"]),
            (RelativeSize.M.value, ["M"]),
            (RelativeSize.L.value, ["L"]),
            ("", [""]),
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
            (RelativeSize.M.value, ["M", ""]),
            ("", ["M", ""]),
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
        data = {"rooms__relative_size": [""]}
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
            ("", [""]),
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
            (SeeHearScore._3.value, ["3", ""]),
            ("", ["4", ""]),
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
        data = {"rooms__see_hear_score": [""]}
        assert test_shul in ShulFilterSet(data, request=test_request).qs


def describe_translated_choices():
    """
    ShulFilterSet's choices are declared at class-body level, which only runs once, at
    import time. If choices were built eagerly there (e.g. `choices=KaddishPolicy.get_...()`
    instead of `choices=lambda: KaddishPolicy.get_...()`), they'd freeze in whatever
    language happened to be active the first time this module was imported, and never
    reflect the active language on any later request.
    """

    def kaddish_policy_choice_labels_reflect_the_active_language(test_request):
        with translation.override("en"):
            en_choices = dict(
                ShulFilterSet(data={}, request=test_request).form.fields["kaddish_policy"].choices
            )
        with translation.override("he"):
            he_choices = dict(
                ShulFilterSet(data={}, request=test_request).form.fields["kaddish_policy"].choices
            )

        assert "Can say alone" in en_choices[KaddishPolicy.CAN_SAY_ALONE.value]
        assert "אפשר לומר לבד" in he_choices[KaddishPolicy.CAN_SAY_ALONE.value]


def describe_kaddish_policy_filter():
    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (KaddishPolicy.CAN_SAY_ALONE.value, ["CAN_SAY_ALONE"]),
            (KaddishPolicy.SHUL_ENSURES_MAN.value, ["SHUL_ENSURES_MAN"]),
            (KaddishPolicy.ONLY_IF_MAN.value, ["ONLY_IF_MAN"]),
            (KaddishPolicy.NO.value, ["NO"]),
            ("", [""]),
        ],
    )
    def includes_shuls_that_match_single_value(test_shul, test_request, value, query):
        Shul.objects.filter(pk=test_shul.pk).update(kaddish_policy=value)

        data = {"kaddish_policy": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (KaddishPolicy.NO.value, ["NO", "ONLY_IF_MAN"]),
            ("", ["NO", ""]),
        ],
    )
    def includes_shuls_that_match_any_of_multiple_values(test_shul, test_request, value, query):
        Shul.objects.filter(pk=test_shul.pk).update(kaddish_policy=value)

        data = {"kaddish_policy": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (KaddishPolicy.NO.value, ["CAN_SAY_ALONE", "ONLY_IF_MAN"]),
            ("", ["CAN_SAY_ALONE", "NO"]),
        ],
    )
    def excludes_shuls_that_do_not_match_any_value(test_shul, test_request, value, query):
        Shul.objects.filter(pk=test_shul.pk).update(kaddish_policy=value)

        data = {"kaddish_policy": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 0
