# -*- encoding: utf-8 -*-


from django import template

register = template.Library()


@register.simple_tag(name="canclaim")
def canclaim(user, paper):
    return paper.can_be_claimed_by(user)
