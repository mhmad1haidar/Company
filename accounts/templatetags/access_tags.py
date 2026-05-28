from django import template


register = template.Library()


@register.filter
def has_module_access(user, module):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    checker = getattr(user, "has_module_access", None)
    if callable(checker):
        return checker(module)
    return False
