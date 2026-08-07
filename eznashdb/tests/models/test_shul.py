import pytest
from django.template import Context, Template

from eznashdb.models import Shul


def describe_cluster_key():
    def matches_the_template_rendered_display_coords():
        """
        The endpoint round-trips this string: JS reads it from the page, sends
        it back as-is, and the server matches it against shul.cluster_key. If
        the two ever diverge, clicking a pin silently does nothing.
        """
        shul = Shul.objects.create(name="S", latitude=40.7128, longitude=-74.0060)

        rendered = Template("{{ shul.cluster_key }}").render(Context({"shul": shul}))

        assert rendered == shul.cluster_key

    def matches_even_when_python_str_would_use_scientific_notation():
        """
        Regression: Django's numberformat expands a float's scientific
        notation (e.g. str() gives "-2e-05" but the template renders
        "-0.00002"). cluster_key must render as a plain string so the two
        never diverge - this shul's fuzzed longitude hits that case.
        """
        shul = Shul.objects.create(name="S", latitude=51.82, longitude=0.001)

        assert "e" in str(shul.display_lon)  # sanity check this case is real
        rendered = Template("{{ shul.cluster_key }}").render(Context({"shul": shul}))

        assert rendered == shul.cluster_key


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
