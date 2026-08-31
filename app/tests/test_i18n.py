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
    Hebrew while the flag is off.
    """

    @override_flag("hebrew_translation", active=False)
    def it_ignores_the_accept_language_header_when_flag_inactive(client):
        response = client.get("/", HTTP_ACCEPT_LANGUAGE="he")

        assert "Mapping women's spaces in synagogues around the world" in response.content.decode()

    @override_flag("hebrew_translation", active=True)
    def it_honors_the_accept_language_header_when_flag_active(client):
        response = client.get("/", HTTP_ACCEPT_LANGUAGE="he")

        assert "מיפוי עזרות נשים בבתי כנסת ברחבי העולם" in response.content.decode()


def describe_javascript_catalog():
    @override_flag("hebrew_translation", active=True)
    def it_serves_the_translated_catalog_for_the_active_language(client):
        client.post("/i18n/setlang/", {"language": "he", "next": "/"})

        response = client.get("/jsi18n/")

        assert response.status_code == 200
        assert "Search name or address..." in response.content.decode()
