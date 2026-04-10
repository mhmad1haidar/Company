from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Intervention, TelecomSite


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    """
    Admin interface for Intervention model with all specified fields
    """
    
    # List display with key fields
    list_display = (
        'codice_nigit', 
        'cliente', 
        'nome',
        'stato_avanzamento_nigit_badge',
        'data_richiesta',
        'tot_richiesto',
        'created_at',
    )
    
    # List filters for key fields
    list_filter = (
        'stato_avanzamento_nigit',
        'stato_avanzamento_contabile_nigit',
        'stato_contabile_sirti',
        'anno_intervento',
        'cliente',
        'data_richiesta',
        'created_at',
    )
    
    # Search fields
    search_fields = (
        'codice_nigit',
        'cliente',
        'nome',
        'assistente',
        'ticket',
        'codice_sito',
        'oda',
    )
    
    # Ordering
    ordering = ('-created_at',)
    
    # Pagination
    list_per_page = 25
    list_max_show_all = 100
    
    # Fieldsets for organized form
    fieldsets = (
        ('Informazioni Principali', {
            'fields': (
                'codice_nigit', 
                'oda', 
                'anno_intervento', 
                'cliente', 
                'nome', 
                'assistente'
            ),
            'classes': ('wide',),
        }),
        ('Dettagli Intervento', {
            'fields': (
                'data_richiesta',
                'tipologia_intervento',
                'ticket',
                'international_code',
                'codice_sito',
                'data_assegnazione_squadra',
            ),
            'classes': ('wide',),
        }),
        ('Stato Avanzamento', {
            'fields': (
                'stato_avanzamento_nigit',
                'stato_avanzamento_contabile_nigit',
                'stato_contabile_sirti',
                'stato_contabile_da_nigit_a_cliente',
            ),
            'classes': ('wide',),
        }),
        ('Date Importanti', {
            'fields': (
                'data_chiusura_lavori',
                'data_invio_preventivo',
                'data_approvazione_preventivo',
            ),
            'classes': ('wide',),
        }),
        ('Informazioni Finanziarie', {
            'fields': (
                'tot_richiesto',
                'importo_autorizzato_sirti',
                'differenza_dare_avere',
                'ses_sirti',
            ),
            'classes': ('wide',),
        }),
        ('Note e Assegnazioni', {
            'fields': (
                'note',
                'assigned_employees',
                'used_car',
            ),
            'classes': ('wide',),
        }),
        ('Informazioni di Sistema', {
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # Filter horizontal for many-to-many
    filter_horizontal = ('assigned_employees',)
    
    # Readonly fields
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    # Optimize queries
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'used_car',
            'created_by'
        ).prefetch_related(
            'assigned_employees'
        )
    
    # Custom display methods
    def stato_avanzamento_nigit_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'DA_INIZIARE': 'orange',
            'IN_CORSO': 'blue',
            'SOSPESO': 'yellow',
            'COMPLETATO': 'green',
            'ANNULLATO': 'red',
        }
        color = colors.get(obj.stato_avanzamento_nigit, 'gray')
        label = obj.get_stato_avanzamento_nigit_display() or 'Non impostato'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            label
        )
    stato_avanzamento_nigit_badge.short_description = 'Stato Avanzamento'
    stato_avanzamento_nigit_badge.admin_order_field = 'stato_avanzamento_nigit'
    
    # Save method
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    # Custom actions
    actions = ['mark_as_completato', 'mark_as_in_corso', 'mark_as_da_iniziare']
    
    def mark_as_completato(self, request, queryset):
        updated = queryset.update(stato_avanzamento_nigit='COMPLETATO')
        self.message_user(request, f'{updated} interventi segnati come Completati.')
    mark_as_completato.short_description = 'Segna come Completato'
    
    def mark_as_in_corso(self, request, queryset):
        updated = queryset.update(stato_avanzamento_nigit='IN_CORSO')
        self.message_user(request, f'{updated} interventi segnati come In Corso.')
    mark_as_in_corso.short_description = 'Segna come In Corso'
    
    def mark_as_da_iniziare(self, request, queryset):
        updated = queryset.update(stato_avanzamento_nigit='DA_INIZIARE')
        self.message_user(request, f'{updated} interventi segnati come Da Iniziare.')
    mark_as_da_iniziare.short_description = 'Segna come Da Iniziare'
    
    # Date hierarchy
    date_hierarchy = 'created_at'


@admin.register(TelecomSite)
class TelecomSiteAdmin(admin.ModelAdmin):
    """
    Admin interface for TelecomSite model
    """
    list_display = ('site_name', 'site_code', 'city', 'region', 'created_at')
    list_filter = ('region', 'province', 'created_at')
    search_fields = ('site_name', 'site_code', 'city', 'address')
    ordering = ('site_name',)
    readonly_fields = ('created_at', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
