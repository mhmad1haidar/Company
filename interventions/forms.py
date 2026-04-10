from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Intervention


class InterventionForm(forms.ModelForm):
    """
    Form for creating and editing interventions
    """
    
    class Meta:
        model = Intervention
        fields = [
            'codice_nigit', 'oda', 'anno_intervento', 'cliente', 'nome', 'assistente',
            'data_richiesta', 'tipologia_intervento', 'ticket', 'international_code',
            'codice_sito', 'data_assegnazione_squadra', 'stato_avanzamento_nigit',
            'stato_avanzamento_contabile_nigit', 'stato_contabile_sirti',
            'stato_contabile_da_nigit_a_cliente', 'note', 'data_chiusura_lavori',
            'data_invio_preventivo', 'data_approvazione_preventivo', 'tot_richiesto',
            'importo_autorizzato_sirti', 'differenza_dare_avere', 'ses_sirti',
            'assigned_employees', 'used_car'
        ]
        widgets = {
            'codice_nigit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Inserisci Codice NIGIT (lasciare vuoto per generare automaticamente)'
            }),
            'oda': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Inserisci ODA'
            }),
            'anno_intervento': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Anno'
            }),
            'cliente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome cliente'
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Intervento'
            }),
            'assistente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome Assistente'
            }),
            'data_richiesta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tipologia_intervento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tipologia intervento'
            }),
            'ticket': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numero ticket'
            }),
            'international_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Codice internazionale'
            }),
            'codice_sito': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Codice sito'
            }),
            'data_assegnazione_squadra': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'stato_avanzamento_nigit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'stato_avanzamento_contabile_nigit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'stato_contabile_sirti': forms.Select(attrs={
                'class': 'form-control'
            }),
            'stato_contabile_da_nigit_a_cliente': forms.Select(attrs={
                'class': 'form-control'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Note aggiuntive...'
            }),
            'data_chiusura_lavori': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'data_invio_preventivo': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'data_approvazione_preventivo': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tot_richiesto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'importo_autorizzato_sirti': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'differenza_dare_avere': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'ses_sirti': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'assigned_employees': forms.SelectMultiple(attrs={
                'class': 'form-control'
            }),
            'used_car': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make required fields more obvious
        required_fields = ['cliente', 'nome']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
        
        # Add help text for important fields
        if 'codice_nigit' in self.fields:
            self.fields['codice_nigit'].help_text = "Codice univoco NIGIT per l'intervento"
        
        if 'tot_richiesto' in self.fields:
            self.fields['tot_richiesto'].help_text = "Importo totale richiesto in €"
        
        if 'importo_autorizzato_sirti' in self.fields:
            self.fields['importo_autorizzato_sirti'].help_text = "Importo autorizzato da Sirti in €"


class InterventionSearchForm(forms.Form):
    """
    Form for searching interventions
    """
    
    SEARCH_CHOICES = [
        ('', 'Tutti i campi'),
        ('codice_nigit', 'Codice NIGIT'),
        ('cliente', 'Cliente'),
        ('nome', 'Nome'),
        ('assistente', 'Assistente'),
        ('ticket', 'Ticket'),
        ('codice_sito', 'Codice Sito'),
        ('oda', 'ODA'),
    ]
    
    search_field = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search_value = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cerca...'
        })
    )
    
    stato_avanzamento = forms.ChoiceField(
        choices=[('', 'Tutti')] + Intervention.STATO_AVANZAMENTO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    anno_intervento = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Anno'
        })
    )
    
    cliente_filter = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtra per cliente...'
        })
    )


class InterventionImportForm(forms.Form):
    """
    Form for importing interventions from CSV/Excel
    """
    
    file = forms.FileField(
        label=_('File CSV/Excel'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        help_text=_('Carica un file CSV o Excel con gli interventi da importare')
    )
    
    overwrite_existing = forms.BooleanField(
        label=_('Sovrascrivi interventi esistenti'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text=_('Se selezionato, gli interventi con lo stesso Codice NIGIT verranno sovrascritti')
    )
