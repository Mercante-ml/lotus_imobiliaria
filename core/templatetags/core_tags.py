import json
from django.template import Library
from django.utils.safestring import mark_safe

register = Library()

@register.filter(is_safe=True)
def json_script(value, element_id):
    """
    Escape and serialize a Python object to JSON, and wrap it in a script tag.
    """
    from django.core.serializers.json import DjangoJSONEncoder
    json_str = json.dumps(list(value), cls=DjangoJSONEncoder)
    return mark_safe(f'<script id="{element_id}" type="application/json">{json_str}</script>')

@register.simple_tag
def get_favorite_ids(user):
    if user.is_authenticated:
        return list(user.profile.favoritos.values_list('id', flat=True))
    return []
