from django import template

register = template.Library()

@register.filter
def abs_val(value):
    try:
        return abs(int(value))
    except (TypeError, ValueError):
        return value
