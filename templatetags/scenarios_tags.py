from django import template
from django.utils.safestring import mark_safe
from django.templatetags.static import static

register = template.Library()

@register.filter
def yesnoicons(value):
    """
    Returns an icon for boolean values.
    """
    if value:
        return mark_safe(f'<img src="{static("img/yes.png")}" alt="Yes" />')
    return mark_safe(f'<img src="{static("img/no.png")}" alt="No" />') 