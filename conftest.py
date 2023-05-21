from typing import Callable

import pytest
from django.core.handlers.wsgi import WSGIRequest
from django.urls import resolve, reverse

from eznashdb.constants import DEFAULT_ARG


@pytest.fixture(autouse=True)
def _override_settings_for_testing(settings):
    settings.STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"


@pytest.fixture(autouse=True)
def _enable_db_access_for_all_tests(db):
    pass


@pytest.fixture()
def test_user(django_user_model):
    user = django_user_model.objects.create(
        username="test_user",
    )
    user.set_password("password")
    return user


@pytest.fixture()
def rf_GET(rf) -> Callable:
    def _GET_request(view_name: str, params: dict = DEFAULT_ARG) -> WSGIRequest:
        if params == DEFAULT_ARG:
            params = {}
        url = reverse(view_name)
        request = rf.get(url, params)
        request.resolver_match = resolve(url)
        return request

    return _GET_request
