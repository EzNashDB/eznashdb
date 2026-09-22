from django.conf import settings


def describe_set_language():
    def it_allows_switching_to_hebrew(client):
        response = client.post("/i18n/setlang/", {"language": "he", "next": "/"})

        assert response.status_code == 302
        assert client.cookies[settings.LANGUAGE_COOKIE_NAME].value == "he"

    def it_allows_switching_to_english(client):
        response = client.post("/i18n/setlang/", {"language": "en", "next": "/"})

        assert response.status_code == 302
        assert client.cookies[settings.LANGUAGE_COOKIE_NAME].value == "en"


def describe_language_negotiation():
    def it_honors_the_accept_language_header(client):
        response = client.get("/", HTTP_ACCEPT_LANGUAGE="he", follow=True)

        assert response.redirect_chain == [("/he/", 302)]
        assert "מיפוי עזרות נשים בבתי כנסת ברחבי העולם" in response.content.decode()

    def it_serves_a_hebrew_prefixed_url(client):
        response = client.get("/he/")

        assert response.status_code == 200


def describe_admin_english_only():
    """
    Django's contrib.admin ships its own Hebrew catalog, so without this gate a
    Hebrew-negotiated request (Accept-Language, or the language cookie) would render a
    half-translated, RTL admin UI.
    """

    def it_forces_english_on_the_admin_login_page_even_with_hebrew_negotiated(client):
        client.post("/i18n/setlang/", {"language": "he", "next": "/"})

        response = client.get("/admin/login/", HTTP_ACCEPT_LANGUAGE="he")

        content = response.content.decode()
        assert '<html lang="en"' in content
        assert "Log in" in content

    def it_leaves_non_admin_pages_in_the_negotiated_language(client):
        client.post("/i18n/setlang/", {"language": "he", "next": "/"})

        response = client.get("/he/")

        assert response.status_code == 200
        assert '<html lang="he" dir="rtl">' in response.content.decode()


def describe_rtl_layout():
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
    def it_serves_the_translated_catalog_for_the_active_language(client):
        client.post("/i18n/setlang/", {"language": "he", "next": "/he/"})

        response = client.get("/jsi18n/")

        assert response.status_code == 200
        # This msgid (not its \uXXXX-escaped Hebrew value) only appears when Hebrew is active.
        assert "Search by name or address..." in response.content.decode()
