from django import template
from django.utils.html import format_html

from eznashdb.contact import ContactMethod, parse_contact

register = template.Library()


@register.simple_tag
def contact_link(value):
    """
    Render a shul's contact as a tel:/mailto:/web link. Empty if the value isn't a valid contact.

    Each piece is wrapped in <bdi> so numbers and URLs keep their left-to-right order, and any
    trailing text keeps its own direction, when embedded in right-to-left (Hebrew) text.
    """
    contact = parse_contact(value)
    if contact is None:
        return ""
    # `rel`/`target` only matter for web links, but are harmless on tel:/mailto:
    link = format_html(
        '<a href="{}" rel="nofollow noopener noreferrer ugc"{}><bdi dir="ltr">{}</bdi></a>',
        contact.href,
        format_html(' target="_blank"') if contact.method == ContactMethod.URL else "",
        contact.text,
    )
    if contact.trailing_text:
        return format_html("{} <bdi>{}</bdi>", link, contact.trailing_text)
    return link
