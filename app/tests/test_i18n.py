from django.conf import settings
from waffle.testutils import override_flag


def describe_set_language():
    @override_flag("hebrew_translation", active=False)
    def it_ignores_non_english_languages_when_flag_inactive(client):
        response = client.post("/i18n/setlang/", {"language": "he", "next": "/"})

        assert response.status_code == 302
        assert response.url == "/"
        cookie = client.cookies.get(settings.LANGUAGE_COOKIE_NAME)
        assert cookie is None or cookie.value != "he"

    @override_flag("hebrew_translation", active=True)
    def it_allows_switching_to_hebrew_when_flag_active(client):
        response = client.post("/i18n/setlang/", {"language": "he", "next": "/"})

        assert response.status_code == 302
        assert client.cookies[settings.LANGUAGE_COOKIE_NAME].value == "he"

    @override_flag("hebrew_translation", active=False)
    def it_always_allows_switching_to_english(client):
        response = client.post("/i18n/setlang/", {"language": "en", "next": "/"})

        assert response.status_code == 302
        assert client.cookies[settings.LANGUAGE_COOKIE_NAME].value == "en"


def describe_hebrew_translation_gate():
    """
    LocaleMiddleware negotiates language from several independent sources - not just
    the cookie set_language controls. This locks in that none of them can activate
    Hebrew while the flag is off, and that a direct "/he/..." request is a hard 404
    rather than being silently served in English at a URL that claims Hebrew.
    """

    @override_flag("hebrew_translation", active=False)
    def it_ignores_the_accept_language_header_when_flag_inactive(client):
        response = client.get("/", HTTP_ACCEPT_LANGUAGE="he", follow=True)

        assert response.redirect_chain == [("/en/", 302)]
        assert "Mapping women's spaces in synagogues around the world" in response.content.decode()

    @override_flag("hebrew_translation", active=True)
    def it_honors_the_accept_language_header_when_flag_active(client):
        response = client.get("/", HTTP_ACCEPT_LANGUAGE="he", follow=True)

        assert response.redirect_chain == [("/he/", 302)]
        assert "מיפוי עזרות נשים בבתי כנסת ברחבי העולם" in response.content.decode()

    @override_flag("hebrew_translation", active=False)
    def it_404s_a_direct_request_for_a_hebrew_prefixed_url(client):
        response = client.get("/he/")

        assert response.status_code == 404

    @override_flag("hebrew_translation", active=True)
    def it_serves_a_hebrew_prefixed_url_when_flag_active(client):
        response = client.get("/he/")

        assert response.status_code == 200


def describe_rtl_layout():
    @override_flag("hebrew_translation", active=True)
    def it_marks_hebrew_pages_dir_rtl_and_loads_the_rtl_bootstrap_build(client):
        content = client.get("/he/").content.decode()

        # An exact match matters here, not just presence: `dir` is an HTML enumerated
        # attribute, so surrounding whitespace (e.g. from a `{% if %}` split across
        # lines) makes it an invalid value that silently falls back to ltr.
        assert '<html lang="he" dir="rtl">' in content
        assert "bootstrap.rtl.min.css" in content
        assert "vendor/bootstrap-5.3.0/bootstrap.min.css" not in content

    def it_marks_english_pages_dir_ltr_and_loads_the_ltr_bootstrap_build(client):
        content = client.get("/en/").content.decode()

        assert '<html lang="en" dir="ltr">' in content
        assert "vendor/bootstrap-5.3.0/bootstrap.min.css" in content
        assert "bootstrap.rtl.min.css" not in content


def describe_javascript_catalog():
    @override_flag("hebrew_translation", active=True)
    def it_serves_the_translated_catalog_for_the_active_language(client):
        client.post("/i18n/setlang/", {"language": "he", "next": "/he/"})

        response = client.get("/jsi18n/")

        assert response.status_code == 200
        # This msgid (not its \uXXXX-escaped Hebrew value) only appears when Hebrew is active.
        assert "Search by name or address..." in response.content.decode()
