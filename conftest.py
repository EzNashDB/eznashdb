import pytest
from django.urls import resolve, reverse
from django.core.handlers.wsgi import WSGIRequest
from typing import Callable

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

@pytest.fixture()
def GET_request_factory(rf) -> Callable:
    def _GET_request(view_name: str) -> WSGIRequest:
        url = reverse(view_name)
        request = (rf.get(url))
        request.resolver_match = resolve(url)
        return request
    return _GET_request
