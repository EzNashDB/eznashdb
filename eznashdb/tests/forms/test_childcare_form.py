import pytest

from eznashdb.forms import ChildcareProgramForm
from eznashdb.models import Shul


def describe_validation():
    @pytest.mark.parametrize(
        ("min_age", "max_age", "is_valid"),
        [
            (1, 2, True),
            (1, 1, True),
            (2, 1, False),
        ],
    )
    def min_age_is_less_than_max_age(min_age, max_age, is_valid):
        shul = Shul.objects.create()
        form = ChildcareProgramForm(
            data={
                "shul": shul,
                "name": "test program",
                "min_age": min_age,
                "max_age": max_age,
            }
        )
        form.is_valid()

        assert ("min_age" in form.errors) is not is_valid
