from eznashdb.models import ChildcareProgram, Shul


def test_default_ordering_is_min_age_then_max():
    shul = Shul.objects.create()
    prog_3 = ChildcareProgram.objects.create(shul=shul, min_age=6, max_age=7)
    prog_1 = ChildcareProgram.objects.create(shul=shul, min_age=0, max_age=5)
    prog_2 = ChildcareProgram.objects.create(shul=shul, min_age=1, max_age=4)

    assert list(ChildcareProgram.objects.all()) == [prog_1, prog_2, prog_3]
