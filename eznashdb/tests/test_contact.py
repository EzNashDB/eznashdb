import pytest

from eznashdb.contact import ContactMethod, parse_contact


def describe_parse_contact():
    @pytest.mark.parametrize(
        ("value", "method"),
        [
            ("rabbi@example.org", ContactMethod.EMAIL),
            ("https://example.org/contact", ContactMethod.URL),
            ("example.org", ContactMethod.URL),
            ("www.example.org/about", ContactMethod.URL),
            ("123.com", ContactMethod.URL),
            ("212-555-1234", ContactMethod.PHONE),
            ("+972 3-555-1234", ContactMethod.PHONE),
            ("(212) 555.1234", ContactMethod.PHONE),
        ],
    )
    def detects_method_from_value(value, method):
        assert parse_contact(value).method == method

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "   ",
            "hello",
            "123 Main St",
            "555-12",  # too few digits to be a phone number
            "555-12 x5",  # ...even with trailing text
            "javascript:alert(1)",
            "ftp://example.org",  # only http(s) links
            "212-555-1234 or me@example.org",  # an "@" means it has to be a valid email
        ],
    )
    def returns_none_when_not_a_contact(value):
        assert parse_contact(value) is None

    @pytest.mark.parametrize(
        ("value", "href"),
        [
            ("rabbi@example.org", "mailto:rabbi@example.org"),
            ("example.org", "http://example.org"),  # the browser upgrades to https if it can
            ("https://example.org", "https://example.org"),
            ("http://example.org", "http://example.org"),
            ("(212) 555-1234", "tel:2125551234"),
            ("+972 3-555-1234", "tel:+97235551234"),
            ("03-555-1234", "tel:035551234"),  # a country code is never guessed
        ],
    )
    def builds_the_link_target_based_on_contact_method(value, href):
        assert parse_contact(value).href == href

    def never_rewrites_what_the_user_typed():
        contact = parse_contact("  (212) 555-1234  ")

        assert contact.text == "(212) 555-1234"
        assert contact.trailing_text == ""

    @pytest.mark.parametrize("tail", ["x5", "ext. 5", "שלוחה 5", "ask for Dovid", "(office)"])
    def splits_off_any_text_after_a_phone_number(tail):
        contact = parse_contact(f"212-555-1234 {tail}")

        assert contact.method == ContactMethod.PHONE
        assert contact.text == "212-555-1234"
        assert contact.trailing_text == tail
        assert contact.href == "tel:2125551234"
