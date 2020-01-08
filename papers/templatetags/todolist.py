from django import template

register = template.Library()

@register.simple_tag(name='todolist')
def todolist(user, paper):
    return paper.on_todolist(user)
