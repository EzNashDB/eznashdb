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


def describe_shul_name():
    @pytest.mark.parametrize(
        ("name", "query"),
        [
            ("Test Shul", "test shul"),
            ("Test Shul", "ST SH"),
            ("Test Shul", "TeSt sHuL"),
        ],
    )
    def includes_shuls_with_substring_in_name(test_request, name, query):
        Shul.objects.create(name=name)

        assert ShulFilterSet({"name": query}, request=test_request).qs.count() == 1

    def excludes_shuls_that_do_not_have_substring_in_name():
        Shul.objects.create(name="test shul")

        assert ShulFilterSet({"name": "no match"}, request=test_request).qs.count() == 0


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
    def test_includes_shuls_that_match_single_value(self, test_request, value, query):
        Shul.objects.create(**{self.shul_model_field: value})

        assert ShulFilterSet({self.shul_model_field: query}, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, ["True", "False"]),
            (False, ["False", "--"]),
            (None, ["True", "--"]),
        ],
    )
    def test_includes_shuls_that_match_any_of_multiple_values(self, test_request, value, query):
        Shul.objects.create(**{self.shul_model_field: value})

        assert ShulFilterSet({self.shul_model_field: query}, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (True, ["False", "--"]),
            (False, ["True", "--"]),
            (None, ["True", "False"]),
        ],
    )
    def test_excludes_shuls_that_do_not_match_any_value(self, test_request, value, query):
        Shul.objects.create(**{self.shul_model_field: value})

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
    def includes_shuls_that_match_single_value(test_request, value, query):
        shul = Shul.objects.create()
        shul.rooms.create(relative_size=value)

        data = {"rooms__relative_size": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    def shul_appears_once_if_multiple_rooms_match(test_request):
        shul = Shul.objects.create()
        shul.rooms.create(relative_size=RelativeSize.M.value)
        shul.rooms.create(relative_size=RelativeSize.M.value)

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
    def includes_shuls_that_match_any_of_multiple_values(test_request, value, query):
        shul = Shul.objects.create()
        shul.rooms.create(relative_size=value)

        data = {"rooms__relative_size": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (RelativeSize.M.value, ["L", "S"]),
            (RelativeSize.M.value, ["L", "--"]),
            ("", ["S", "M"]),
        ],
    )
    def excludes_shuls_that_do_not_match_any_value(test_request, value, query):
        shul = Shul.objects.create()
        shul.rooms.create(relative_size=value)

        data = {"rooms__relative_size": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 0

    def unknown_includes_shuls_without_rooms(test_request):
        shul = Shul.objects.create()

        data = {"rooms__relative_size": ["--"]}
        assert shul in ShulFilterSet(data, request=test_request).qs


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
    def includes_shuls_that_match_single_value(test_request, value, query):
        shul = Shul.objects.create()
        shul.rooms.create(see_hear_score=value)

        data = {"rooms__see_hear_score": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    def shul_appears_once_if_multiple_rooms_match(test_request):
        shul = Shul.objects.create()
        shul.rooms.create(see_hear_score=SeeHearScore._3.value)
        shul.rooms.create(see_hear_score=SeeHearScore._3.value)

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
    def includes_shuls_that_match_any_of_multiple_values(test_request, value, query):
        shul = Shul.objects.create()
        shul.rooms.create(see_hear_score=value)

        data = {"rooms__see_hear_score": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("value", "query"),
        [
            (SeeHearScore._3.value, ["4", "5"]),
            (SeeHearScore._3.value, ["4", "--"]),
            ("", ["4", "3"]),
        ],
    )
    def excludes_shuls_that_do_not_match_any_value(test_request, value, query):
        shul = Shul.objects.create()
        shul.rooms.create(see_hear_score=value)

        data = {"rooms__see_hear_score": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 0

    def unknown_includes_shuls_without_rooms(test_request):
        shul = Shul.objects.create()

        data = {"rooms__see_hear_score": ["--"]}
        assert shul in ShulFilterSet(data, request=test_request).qs


def describe_room_layout_filter():
    @pytest.mark.parametrize(
        ("layout_field", "query"),
        [
            ("is_same_height_side",) * 2,
            ("is_same_height_back",) * 2,
            ("is_elevated_side",) * 2,
            ("is_elevated_back",) * 2,
            ("is_balcony",) * 2,
            ("is_only_men",) * 2,
            ("is_mixed_seating",) * 2,
            ("", ["--"]),
        ],
    )
    def includes_shuls_that_match_single_value(test_request, layout_field, query):
        shul = Shul.objects.create()
        room = shul.rooms.create()
        if layout_field:
            setattr(room, layout_field, True)
            room.save()

        data = {"rooms__layout": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    def shul_appears_once_if_multiple_rooms_match(test_request):
        shul = Shul.objects.create()
        shul.rooms.create(is_same_height_back=True)
        shul.rooms.create(is_same_height_back=True)

        data = {"rooms__layout": ["is_same_height_back"]}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("layout_field", "query"),
        [
            ("is_same_height_side", ["is_same_height_side", "is_balcony"]),
            ("is_same_height_side", ["is_same_height_side", "--"]),
            ("", ["is_same_height_side", "--"]),
        ],
    )
    def includes_shuls_that_match_any_of_multiple_values(test_request, layout_field, query):
        shul = Shul.objects.create()
        room = shul.rooms.create()
        if layout_field:
            setattr(room, layout_field, True)
            room.save()

        data = {"rooms__layout": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 1

    @pytest.mark.parametrize(
        ("layout_field", "query"),
        [
            ("is_same_height_side", ["is_same_height_back", "is_balcony"]),
            ("is_same_height_side", ["is_same_height_back", "--"]),
            ("", ["is_same_height_side", "is_same_height_back"]),
        ],
    )
    def excludes_shuls_that_do_not_match_any_value(test_request, layout_field, query):
        shul = Shul.objects.create()
        room = shul.rooms.create()
        if layout_field:
            setattr(room, layout_field, True)
            room.save()
        data = {"rooms__layout": query}
        assert ShulFilterSet(data, request=test_request).qs.count() == 0

    def unknown_includes_shuls_without_rooms(test_request):
        shul = Shul.objects.create()

        data = {"rooms__layout": ["--"]}
        assert shul in ShulFilterSet(data, request=test_request).qs
