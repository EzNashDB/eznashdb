import pytest

from eznashdb.models import Shul


def describe_get_map_url():
    @pytest.fixture
    def shul(test_user):
        return Shul.objects.create(
            name="Test Shul",
            latitude=31.7767,
            longitude=35.2345,
            created_by=test_user,
        )

    def returns_relative_url_by_default(shul):
        url = shul.get_map_url()

        assert url.startswith("/")
        assert f"selectedShul={shul.pk}" in url
        assert "zoom=17" in url
        assert "lat=" in url
        assert "lon=" in url

    def uses_site_url_setting_when_set(shul, settings):
        settings.SITE_URL = "http://localhost:8000"
        url = shul.get_map_url(absolute=True)

        assert url.startswith("http://localhost:8000")
        assert f"selectedShul={shul.pk}" in url

    def falls_back_to_sites_framework(shul, settings):
        from django.contrib.sites.models import Site

        settings.SITE_URL = None
        site = Site.objects.get_current()
        url = shul.get_map_url(absolute=True)

        assert url.startswith("https://")
        assert site.domain in url
        assert f"selectedShul={shul.pk}" in url
