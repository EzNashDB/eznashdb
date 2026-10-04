from django.template import Context, Template


def render(value):
    return Template("{% load contact %}{% contact_link value %}").render(Context({"value": value}))


def describe_contact_link():
    def renders_a_phone_as_a_tel_link_that_stays_in_the_same_tab():
        html = render("(212) 555-1234")

        assert 'href="tel:2125551234"' in html
        assert '<bdi dir="ltr">(212) 555-1234</bdi>' in html
        assert "_blank" not in html

    def renders_text_after_a_phone_outside_the_link_in_its_own_bdi():
        html = render("212-555-1234 שלוחה 5")

        assert '<bdi dir="ltr">212-555-1234</bdi></a> <bdi>שלוחה 5</bdi>' in html

    def opens_websites_in_a_new_tab_without_passing_on_authority():
        html = render("example.org")

        assert 'href="http://example.org"' in html
        assert 'target="_blank"' in html
        assert 'rel="nofollow noopener noreferrer ugc"' in html

    def escapes_trailing_text():
        assert "<script>" not in render("212-555-1234 <script>alert(1)</script>")

    def renders_nothing_for_an_invalid_or_blank_value():
        assert render("javascript:alert(1)") == ""
        assert render("") == ""
