from django import template

register = template.Library()

@register.filter
def intervention_status_color(status):
    """Return Bootstrap color class based on intervention status"""
    status_colors = {
        'DA_INIZIARE': 'warning',
        'IN_CORSO': 'primary',
        'SOSPESO': 'info',
        'COMPLETATO': 'success',
        'ANNULLATO': 'danger',
        'CHIUSO': 'secondary',
    }
    return status_colors.get(status, 'secondary')

@register.filter
def status_color(status):
    """Return Bootstrap color class based on assignment status (alias for compatibility)"""
    status_colors = {
        'pending': 'warning',
        'assigned': 'info',
        'in_progress': 'primary',
        'completed': 'success',
        'not_worked': 'danger',
        'cancelled': 'secondary',
    }
    return status_colors.get(status, 'secondary')
