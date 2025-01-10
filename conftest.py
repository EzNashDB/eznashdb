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


@pytest.fixture
def test_user(django_user_model):
    user = django_user_model.objects.create(
        username="test_user",
    )
    user.set_password("password")
    return user


@pytest.fixture
def rf_GET(rf) -> Callable:
    def _GET_request(
        view_name: str, url_params: dict = DEFAULT_ARG, query_params: dict = DEFAULT_ARG
    ) -> WSGIRequest:
        if url_params == DEFAULT_ARG:
            url_params = {}
        if query_params == DEFAULT_ARG:
            query_params = {}
        url = reverse(view_name, kwargs=url_params)
        request = rf.get(url, query_params)
        request.resolver_match = resolve(url)
        return request

    return _GET_request
