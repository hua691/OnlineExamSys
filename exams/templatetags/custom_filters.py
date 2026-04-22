"""自定义模板过滤器（Django 要求放在 <app>/templatetags/ 下才能被 {% load %} 识别）。"""
from django import template

register = template.Library()


@register.filter(name='mul')
def mul(value, arg):
    """乘法过滤器：value * arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0.0


@register.filter(name='dict_get')
def dict_get(d, key):
    """从字典取值,兼容 int/str key（Django 模板字典对 int key 不友好）。"""
    if not isinstance(d, dict):
        return ''
    if key in d:
        return d[key]
    s = str(key)
    if s in d:
        return d[s]
    try:
        return d[int(key)]
    except (TypeError, ValueError, KeyError):
        return ''


@register.filter(name='csv_has')
def csv_has(csv_str, item):
    """判断逗号分隔字符串是否包含指定 item(避免 substring 误判)。

    使用:{% if 'A,B'|csv_has:'A' %}yes{% endif %}
    """
    if not csv_str:
        return False
    parts = [s.strip() for s in str(csv_str).split(',')]
    return str(item) in parts
