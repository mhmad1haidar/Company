from django import forms
from django.utils.translation import gettext_lazy as _
import unicodedata
from .models import CorrectiveReport, Intervention


CORRECTIVE_REPORT_COLUMNS = [
    "Indirizzo email",
    "Cliente",
    "REGIONE",
    "Nome assistente e recapito telefonico",
    "Nome ordinante",
    "Cod. sito",
    "NOME SITO BTS",
    "Tipo manutenzione",
    "Tipo Manutenzione Altro",
    "Cod. intervento / Num. scheda gig",
    "Data richiesta intervento",
    "Personale presente",
    "Veicolo Aziendale",
    "Richiesta Cliente",
    "Descrizione intervento",
    "Data esecuzione lavori",
    "Intervento risolutivo?",
    "Richiesta sospensione",
    "Descrivere la causa della sospensione",
    "Data",
    "Inizio lavori",
    "Fine lavori",
    "Cod_Nigit",
    "Presente squadra di supporto?",
    "Personale presente supporto",
    "Veicolo Aziendale supporto",
    "Cod. internazionale",
    "Personale presente supporto 2",
    "Materiale utilizzato 1",
    "Materiale utilizzato 2",
    "Materiale utilizzato 3",
    "Materiale utilizzato 4",
    "Materiale utilizzato 5",
    "Quantità1",
    "Quantità2",
    "Quantità3",
    "Quantità4",
    "Quantità5",
    "Materiale Non presente nella lista 1",
    "Quantità1-1",
    "Materiale Non presente nella lista 2",
    "Quantità2-2",
    "Materiale Non presente nella lista 3",
    "Quantità3-3",
    "Confirmation",
    "Indirizzio",
    "Elenco Materiale necessarie per completare il lavoro :",
    "SENT",
]


def _question_key(label):
    normalized = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode("ascii")
    return "q_" + "".join(ch.lower() if ch.isalnum() else "_" for ch in normalized).strip("_")


class CorrectiveReportForm(forms.ModelForm):
    """Corrective report form generated from the Excel report columns."""

    QUESTION_FIELDS = [(label, _question_key(label)) for label in CORRECTIVE_REPORT_COLUMNS]

    class Meta:
        model = CorrectiveReport
        fields = [
            "performed_at",
            "fault_found",
            "action_taken",
            "work_summary",
            "customer_notes",
            "internal_notes",
        ]
        widgets = {
            "performed_at": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "fault_found": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "action_taken": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "work_summary": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "customer_notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "internal_notes": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, intervention=None, **kwargs):
        self.intervention = intervention or getattr(kwargs.get("instance"), "intervention", None)
        super().__init__(*args, **kwargs)

        if not self.intervention:
            self.fields["codice_nigit_lookup"] = forms.CharField(
                label="Codice NIGIT",
                required=True,
                widget=forms.TextInput(attrs={
                    "class": "form-control corrective-code-lookup",
                    "placeholder": "Enter Codice NIGIT",
                    "autocomplete": "off",
                }),
            )

        existing_answers = getattr(self.instance, "answers", None) or {}
        defaults = self._intervention_defaults()
        for label, key in self.QUESTION_FIELDS:
            field = self._build_question_field(label)
            field.initial = existing_answers.get(label, defaults.get(label, ""))
            self.fields[key] = field

    def clean_codice_nigit_lookup(self):
        code = self.cleaned_data.get("codice_nigit_lookup", "").strip()
        if self.intervention:
            return code
        try:
            self.intervention = Intervention.objects.get(codice_nigit__iexact=code)
        except Intervention.DoesNotExist as exc:
            raise forms.ValidationError("No intervention found with this Codice NIGIT.") from exc
        return code

    def _build_question_field(self, label):
        attrs = {"class": "form-control", "placeholder": label}
        lower = label.lower()
        if "data" in lower:
            return forms.DateField(label=label, required=False, widget=forms.DateInput(attrs={**attrs, "type": "date"}))
        if "inizio lavori" in lower or "fine lavori" in lower:
            return forms.TimeField(label=label, required=False, widget=forms.TimeInput(attrs={**attrs, "type": "time"}))
        if "quantità" in lower:
            return forms.IntegerField(label=label, required=False, min_value=0, widget=forms.NumberInput(attrs=attrs))
        if "risolutivo" in lower or "sospensione" in lower or "supporto?" in lower or label == "Confirmation":
            return forms.ChoiceField(
                label=label,
                required=False,
                choices=[("", "---------"), ("yes", "Yes"), ("no", "No")],
                widget=forms.Select(attrs={"class": "form-select"}),
            )
        rows = 2 if any(word in lower for word in ["richiesta", "descrizione", "elenco", "causa"]) else 1
        if rows > 1:
            return forms.CharField(label=label, required=False, widget=forms.Textarea(attrs={**attrs, "rows": rows}))
        return forms.CharField(label=label, required=False, widget=forms.TextInput(attrs=attrs))

    def _intervention_defaults(self):
        intervention = self.intervention
        if not intervention:
            return {}
        return {
            "Cliente": intervention.cliente or "",
            "Nome assistente e recapito telefonico": intervention.assistente or "",
            "Cod. sito": intervention.codice_sito or "",
            "NOME SITO BTS": intervention.nome or "",
            "Tipo manutenzione": intervention.tipologia_intervento or "",
            "Cod. intervento / Num. scheda gig": intervention.ticket or "",
            "Data richiesta intervento": intervention.data_richiesta,
            "Veicolo Aziendale": str(intervention.used_car) if intervention.used_car else "",
            "Richiesta Cliente": intervention.note or "",
            "Cod_Nigit": intervention.codice_nigit or "",
            "Cod. internazionale": intervention.international_code or "",
        }

    def save(self, commit=True):
        report = super().save(commit=False)
        answers = {}
        for label, key in self.QUESTION_FIELDS:
            value = self.cleaned_data.get(key)
            if value in [None, ""]:
                continue
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            answers[label] = value
        report.answers = answers
        if commit:
            report.save()
        return report


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
