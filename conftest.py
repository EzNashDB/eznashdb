import pytest

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass

@pytest.fixture()
def test_user(django_user_model):
    user = django_user_model.objects.create(
        username="test_user",
    )
    user.set_password("password")
    return user