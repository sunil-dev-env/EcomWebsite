# your_app/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return format(float(value) * float(arg), '.2f')
    except (ValueError, TypeError):
        return ''
