from django import template

register = template.Library()

@register.filter
def status_color(value):
    """Return Bootstrap color class for assignment status"""
    status_colors = {
        'pending': 'warning',
        'assigned': 'info',
        'in_progress': 'primary',
        'completed': 'success',
        'cancelled': 'danger'
    }
    return status_colors.get(value, 'secondary')

@register.filter
def dict_value(dictionary, key):
    """Get value from dictionary by key"""
    return dictionary.get(key, [])
