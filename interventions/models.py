from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class TelecomSite(models.Model):
    """
    Model for storing telecom sites data
    """
    site_name = models.CharField(max_length=200, verbose_name="Site Name")
    site_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Site Code")
    area = models.CharField(max_length=100, blank=True, null=True, verbose_name="Area")
    region = models.CharField(max_length=100, blank=True, null=True, verbose_name="Region")
    province = models.CharField(max_length=100, blank=True, null=True, verbose_name="Province")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="City")
    address = models.CharField(max_length=500, verbose_name="Address")
    latitude = models.DecimalField(max_digits=10, decimal_places=8, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, verbose_name="Longitude")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Created By")
    
    class Meta:
        verbose_name = "Telecom Site"
        verbose_name_plural = "Telecom Sites"
        ordering = ['site_name']
    
    def __str__(self):
        return self.site_name

class Intervention(models.Model):
    """
    Comprehensive Intervention model for tracking telecom site interventions
    """
    # Internal fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='interventions_created')
    
    # Main intervention fields
    codice_nigit = models.CharField(max_length=50, verbose_name="Codice NIGIT", db_index=True, blank=True, null=True, unique=False)
    oda = models.CharField(max_length=100, verbose_name="ODA", blank=True)
    anno_intervento = models.IntegerField(verbose_name="Anno", null=True, blank=True, db_index=True)
    cliente = models.CharField(max_length=200, verbose_name="Cliente", db_index=True, blank=True, null=True)
    nome = models.CharField(max_length=200, verbose_name="Intervento", blank=True, null=True)
    assistente = models.CharField(max_length=200, verbose_name="Nome Assistente", blank=True)
    data_richiesta = models.DateField(verbose_name="Data Richiesta", null=True, blank=True, db_index=True)
    tipologia_intervento = models.CharField(max_length=100, verbose_name="Tipologia Intervento", blank=True)
    ticket = models.CharField(max_length=100, verbose_name="Ticket", blank=True)
    international_code = models.CharField(max_length=50, verbose_name="International Code", blank=True)
    codice_sito = models.CharField(max_length=50, verbose_name="Codice Sito", blank=True, db_index=True)
    data_assegnazione_squadra = models.DateField(verbose_name="Data Assegnazione Squadra", null=True, blank=True)
    extra_info = models.CharField(max_length=200, verbose_name="Extra Info", blank=True)  # For the unmapped column
    
    # Status fields with dropdown options
    STATO_AVANZAMENTO_CHOICES = [
        ('', '---------'),
        ('DA_INIZIARE', 'Da Iniziare'),
        ('IN_CORSO', 'In Corso'),
        ('SOSPESO', 'Sospeso'),
        ('COMPLETATO', 'Completato'),
        ('ANNULLATO', 'Annullato'),
    ]
    stato_avanzamento_nigit = models.CharField(
        max_length=20, 
        choices=STATO_AVANZAMENTO_CHOICES, 
        verbose_name="Stato Avanzamento NIGIT", 
        blank=True,
        db_index=True
    )
    
    STATO_CONTABILE_CHOICES = [
        ('', '---------'),
        ('DA_EMETTERE', 'Da Emettere'),
        ('EMESSO', 'Emesso'),
        ('INVIATO', 'Inviato'),
        ('APPROVATO', 'Approvato'),
        ('PAGATO', 'Pagato'),
        ('CONTABILIZZATO', 'Contabilizzato'),
    ]
    stato_avanzamento_contabile_nigit = models.CharField(
        max_length=20, 
        choices=STATO_CONTABILE_CHOICES, 
        verbose_name="Stato Avanzamento Contabile NIGIT", 
        blank=True,
        db_index=True
    )
    
    stato_contabile_sirti = models.CharField(
        max_length=20, 
        choices=STATO_CONTABILE_CHOICES, 
        verbose_name="Stato Contabile Sirti", 
        blank=True,
        db_index=True
    )
    
    stato_contabile_da_nigit_a_cliente = models.CharField(
        max_length=20, 
        choices=STATO_CONTABILE_CHOICES, 
        verbose_name="Stato Contabile da NIGIT a Cliente", 
        blank=True,
        db_index=True
    )
    
    # Additional fields
    note = models.TextField(verbose_name="Note", blank=True)
    data_chiusura_lavori = models.DateField(verbose_name="Data Chiusura Lavori", null=True, blank=True)
    data_invio_preventivo = models.DateField(verbose_name="Data Invio Preventivo", null=True, blank=True)
    data_approvazione_preventivo = models.DateField(verbose_name="Data Approvazione Preventivo", null=True, blank=True)
    
    # Financial fields with decimal precision
    tot_richiesto = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Tot Richiesto", 
        null=True, 
        blank=True,
        db_index=True
    )
    importo_autorizzato_sirti = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Importo Autorizzato Sirti", 
        null=True, 
        blank=True
    )
    differenza_dare_avere = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Differenza Dare/Avere", 
        null=True, 
        blank=True
    )
    ses_sirti = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="SES Sirti", 
        null=True, 
        blank=True
    )
    
    # Relationships (keeping existing relationships for compatibility)
    assigned_employees = models.ManyToManyField(
        User, 
        blank=True,
        related_name='interventions_assigned',
        db_index=True
    )
    
    used_car = models.ForeignKey(
        "fleet.Car",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interventions",
        db_index=True
    )
    
    class Meta:
        verbose_name = "Intervention"
        verbose_name_plural = "Interventions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['codice_nigit', 'created_at']),
            models.Index(fields=['cliente', 'anno_intervento']),
            models.Index(fields=['stato_avanzamento_nigit', 'data_richiesta']),
            models.Index(fields=['codice_sito']),
        ]
    
    def __str__(self):
        return f"{self.codice_nigit} - {self.nome} ({self.cliente})"
    
    @property
    def is_overdue(self):
        """Check if intervention is overdue based on dates"""
        if self.data_richiesta and self.stato_avanzamento_nigit not in ['COMPLETATO', 'ANNULLATO']:
            return timezone.now().date() > self.data_richiesta
        return False
    
    @property
    def days_since_request(self):
        """Calculate days since request date"""
        if self.data_richiesta:
            return (timezone.now().date() - self.data_richiesta).days
        return None
    
    @classmethod
    def generate_next_codice_nigit(cls):
        """Generate next Codice NIGIT based on existing codes"""
        from django.db.models import Max
        
        # Get the maximum numeric part for current year (try both formats)
        current_year = timezone.now().year
        year_short = str(current_year)[2:]  # 26 for 2026
        year_prefixes = [f"N{current_year}", f"N0{year_short}"]  # N2026 and N026
        
        max_numeric = 0
        
        for year_prefix in year_prefixes:
            # Find the highest numeric suffix for this prefix
            max_code = cls.objects.filter(
                codice_nigit__startswith=year_prefix
            ).aggregate(
                max_code=Max('codice_nigit')
            )['max_code']
            
            if max_code and max_code.startswith(year_prefix):
                # Extract numeric part
                try:
                    if year_prefix == f"N{current_year}":  # N2026 format
                        numeric_part = int(max_code[5:])  # Skip "N2026"
                    else:  # N026 format
                        numeric_part = int(max_code[4:])  # Skip "N026"
                    max_numeric = max(max_numeric, numeric_part)
                except (ValueError, IndexError):
                    continue
        
        next_numeric = max_numeric + 1
        
        # Use the N026 format to match your existing codes
        return f"N0{year_short}{next_numeric:04d}"
    
    def save(self, *args, **kwargs):
        """Auto-generate Codice NIGIT if empty"""
        if not self.codice_nigit or self.codice_nigit.strip() == '':
            self.codice_nigit = self.generate_next_codice_nigit()
        super().save(*args, **kwargs)
    
    @property
    def financial_summary(self):
        """Calculate financial summary"""
        return {
            'tot_richiesto': self.tot_richiesto or 0,
            'importo_autorizzato': self.importo_autorizzato_sirti or 0,
            'differenza': self.differenza_dare_avere or 0,
            'ses': self.ses_sirti or 0
        }