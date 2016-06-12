from django import template
import re

register = template.Library()


@register.filter
def tag(choice, arg):
    """
    Modifies the attributes of a ChoiceField item.
    Attribute-value pairs are given in the form `attribute="value"`.
    """
    attrs = choice.attrs.copy()
    attrs.update({
        m: n
        for m, n in re.findall(r'(\w+)="(.*?)"', arg)
    })
    return choice.tag(attrs=attrs)
