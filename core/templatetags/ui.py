from django import template
from django.templatetags.static import static
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def icon(name, size=24, cls=""):
    """Inline reference to a symbol in static/img/icons.svg (one cached file for all icons)."""
    return format_html(
        '<svg class="icon {}" width="{}" height="{}" aria-hidden="true" focusable="false">'
        '<use href="{}#{}"></use></svg>',
        cls, size, size, static("img/icons.svg"), name,
    )
