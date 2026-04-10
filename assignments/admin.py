from django.contrib import admin
from .models import WorkAssignment
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(WorkAssignment)
class WorkAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'codice_nigit',
        'get_assigned_to',
        'client_name',
        'status',
        'vehicle',
        'assigned_date',
        'scheduled_date'
    ]
    list_filter = [
        'status',
        'assigned_date',
        'vehicle',
        'assigned_to'
    ]
    search_fields = [
        'codice_nigit',
        'assigned_to__first_name',
        'assigned_to__last_name',
        'assigned_to__username',
        'intervention__cliente',
        'intervention__nome',
        'assignment_note'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'completed_date',
        'assigned_date'
    ]
    
    fieldsets = (
        ('Intervention Details', {
            'fields': ('intervention', 'codice_nigit')
        }),
        ('Assignment Information', {
            'fields': ('assigned_to', 'vehicle', 'assignment_note', 'status')
        }),
        ('Site Information', {
            'fields': ('site_address', 'site_latitude', 'site_longitude'),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'completed_date'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    def get_assigned_to(self, obj):
        """Display assigned users in admin list"""
        users = obj.assigned_to.all()
        if users:
            names = [u.get_full_name() or u.username for u in users[:3]]
            result = ", ".join(names)
            if users.count() > 3:
                result += f" (+{users.count() - 3} more)"
            return result
        return "-"
    get_assigned_to.short_description = 'Assigned To'
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Customize manytomany fields in admin"""
        if db_field.name == 'assigned_to':
            kwargs['queryset'] = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def client_name(self, obj):
        return obj.client_name
    client_name.short_description = 'Client'
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.extend(['intervention', 'codice_nigit'])
        return readonly
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
