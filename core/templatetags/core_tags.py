from django import template

register = template.Library()

@register.filter
def hasattr_filter(obj, attr):
    return hasattr(obj, attr)
