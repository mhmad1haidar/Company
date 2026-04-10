import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from .models import Intervention
from .forms import InterventionForm, InterventionSearchForm, InterventionImportForm
from accounts.models import Notification

User = get_user_model()


class InterventionListView(LoginRequiredMixin, ListView):
    """
    List view for interventions with search and filtering
    """
    model = Intervention
    template_name = 'interventions/intervention_list.html'
    context_object_name = 'interventions'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Intervention.objects.select_related('created_by', 'used_car').prefetch_related('assigned_employees')
        
        # Apply search filters
        search_form = InterventionSearchForm(self.request.GET)
        if search_form.is_valid():
            search_field = search_form.cleaned_data.get('search_field')
            search_value = search_form.cleaned_data.get('search_value')
            stato_avanzamento = search_form.cleaned_data.get('stato_avanzamento')
            anno_intervento = search_form.cleaned_data.get('anno_intervento')
            cliente_filter = search_form.cleaned_data.get('cliente_filter')
            
            if search_value:
                if search_field:
                    # Search in specific field
                    filter_kwargs = {f'{search_field}__icontains': search_value}
                    queryset = queryset.filter(**filter_kwargs)
                else:
                    # Search in all relevant fields
                    queryset = queryset.filter(
                        Q(codice_nigit__icontains=search_value) |
                        Q(cliente__icontains=search_value) |
                        Q(nome__icontains=search_value) |
                        Q(assistente__icontains=search_value) |
                        Q(ticket__icontains=search_value) |
                        Q(codice_sito__icontains=search_value) |
                        Q(oda__icontains=search_value)
                    )
            
            if stato_avanzamento:
                queryset = queryset.filter(stato_avanzamento_nigit=stato_avanzamento)
            
            if anno_intervento:
                queryset = queryset.filter(anno_intervento=anno_intervento)
            
            if cliente_filter:
                queryset = queryset.filter(cliente__icontains=cliente_filter)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = InterventionSearchForm(self.request.GET)
        
        # Add statistics
        interventions = self.get_queryset()
        context['total_interventions'] = interventions.count()
        context['total_value'] = interventions.aggregate(
            total=Sum('tot_richiesto')
        )['total'] or 0
        
        # Status breakdown
        context['status_breakdown'] = interventions.values('stato_avanzamento_nigit').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return context


class InterventionDetailView(LoginRequiredMixin, DetailView):
    """
    Detail view for a single intervention
    """
    model = Intervention
    template_name = 'interventions/intervention_detail.html'
    context_object_name = 'intervention'
    
    def get_queryset(self):
        return Intervention.objects.select_related('created_by', 'used_car').prefetch_related('assigned_employees')


class InterventionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Create view for new interventions
    """
    model = Intervention
    form_class = InterventionForm
    template_name = 'interventions/intervention_form.html'
    success_url = reverse_lazy('interventions:intervention-list')
    permission_required = 'interventions.add_intervention'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        intervention = form.save()
        
        # Notify admins and managers about new intervention
        admins_managers = User.objects.filter(
            Q(is_staff=True) | Q(role__in=[User.Role.ADMIN, User.Role.MANAGER])
        ).distinct()
        
        for admin in admins_managers:
            if admin != self.request.user:
                Notification.objects.create(
                    recipient=admin,
                    notification_type=Notification.NotificationType.INTERVENTION_NEW,
                    title="New Intervention Created",
                    message=f"New intervention {intervention.codice_nigit} - {intervention.nome} has been created.",
                    link=f"/interventions/{intervention.pk}/"
                )
        
        messages.success(self.request, 'Intervento creato con successo!')
        return redirect('interventions:intervention-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuovo Intervento'
        context['action'] = 'create'
        
        # Pre-generate and show the next Codice NIGIT
        next_code = Intervention.generate_next_codice_nigit()
        context['next_codice_nigit'] = next_code
        
        # If form instance exists and has no codice_nigit, set it
        if hasattr(self, 'object') and self.object and not self.object.codice_nigit:
            self.object.codice_nigit = next_code
            form = context.get('form')
            if form:
                form.initial['codice_nigit'] = next_code
        
        return context


class InterventionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Update view for existing interventions
    """
    model = Intervention
    form_class = InterventionForm
    template_name = 'interventions/intervention_form.html'
    success_url = reverse_lazy('interventions:intervention-list')
    permission_required = 'interventions.change_intervention'
    
    def form_valid(self, form):
        intervention = form.save()
        
        # Notify about status change
        old_status = self.object.stato_avanzamento_nigit if self.object else None
        new_status = intervention.stato_avanzamento_nigit
        
        if old_status != new_status:
            # Notify assigned employees
            for employee in intervention.assigned_employees.all():
                if employee != self.request.user:
                    Notification.objects.create(
                        recipient=employee,
                        notification_type=Notification.NotificationType.INTERVENTION_STATUS_CHANGE,
                        title="Intervention Status Updated",
                        message=f"Intervention {intervention.codice_nigit} status changed from {old_status} to {new_status}.",
                        link=f"/interventions/{intervention.pk}/"
                    )
            
            # Notify admins/managers
            admins_managers = User.objects.filter(
                Q(is_staff=True) | Q(role__in=[User.Role.ADMIN, User.Role.MANAGER])
            ).distinct()
            
            for admin in admins_managers:
                if admin != self.request.user:
                    Notification.objects.create(
                        recipient=admin,
                        notification_type=Notification.NotificationType.INTERVENTION_STATUS_CHANGE,
                        title="Intervention Status Updated",
                        message=f"Intervention {intervention.codice_nigit} - {intervention.nome} status changed from {old_status} to {new_status}.",
                        link=f"/interventions/{intervention.pk}/"
                    )
        
        messages.success(self.request, 'Intervento aggiornato con successo!')
        return redirect('interventions:intervention-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifica Intervento'
        context['action'] = 'update'
        return context


class InterventionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Delete view for interventions
    """
    model = Intervention
    template_name = 'interventions/intervention_confirm_delete.html'
    success_url = reverse_lazy('interventions:intervention-list')
    permission_required = 'interventions.delete_intervention'
    
    def delete(self, request, *args, **kwargs):
        intervention = self.get_object()
        messages.success(request, f'Intervento {intervention.codice_nigit} eliminato con successo!')
        return super().delete(request, *args, **kwargs)


@login_required
@permission_required('interventions.delete_intervention')
def bulk_delete_interventions(request):
    """Bulk delete multiple interventions"""
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_interventions')
        
        if not selected_ids:
            messages.warning(request, 'Nessun intervento selezionato per l\'eliminazione.')
            return redirect('interventions:intervention-list')
        
        # Convert string IDs to UUID
        try:
            interventions = Intervention.objects.filter(pk__in=selected_ids)
            count = interventions.count()
            interventions.delete()
            messages.success(request, f'{count} intervento/i eliminato/i con successo!')
        except Exception as e:
            messages.error(request, f'Errore durante l\'eliminazione: {e}')
        
        return redirect('interventions:intervention-list')
    
    return redirect('interventions:intervention-list')


class InterventionImportView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    Import view for interventions from CSV/Excel
    """
    template_name = 'interventions/intervention_import.html'
    form_class = InterventionImportForm
    success_url = reverse_lazy('interventions:intervention-list')
    permission_required = 'interventions.add_intervention'
    
    def form_valid(self, form):
        try:
            file = form.cleaned_data['file']
            overwrite_existing = form.cleaned_data.get('overwrite_existing', False)
            
            # Determine file type and read accordingly
            if file.name.endswith('.csv'):
                interventions_data = self._read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                interventions_data = self._read_excel(file)
            else:
                messages.error(self.request, 'Formato file non supportato. Usa CSV o Excel.')
                return self.form_invalid(form)
            
            # DEBUG: Show what was found in the file
            if interventions_data:
                first_row = interventions_data[0]
                columns_found = list(first_row.keys())
                messages.info(self.request, f'Colonne trovate nel file: {", ".join(columns_found[:10])}... ({len(columns_found)} totali)')
                messages.info(self.request, f'Righe lette dal file: {len(interventions_data)}')
                
                # DEBUG: Check for duplicate Cliente columns (exact matches only)
                cliente_columns = [col for col in columns_found if col.lower() in ['cliente', 'cliente,']]
                if len(cliente_columns) > 1:
                    messages.info(self.request, f'Trovate più colonne Cliente: {", ".join(cliente_columns)} - verranno combinate')
            else:
                messages.warning(self.request, 'Nessuna riga trovata nel file!')
                return self.form_invalid(form)
            
            # Import interventions
            imported_count = self._import_interventions(interventions_data, overwrite_existing)
            
            if imported_count > 0:
                messages.success(self.request, f'Importati con successo {imported_count} interventi!')
            else:
                messages.warning(self.request, 'Nessun intervento importato. Controlla che i dati siano validi e che ci sia la colonna "Codice NIGIT".')
            return super().form_valid(form)
            
        except Exception as e:
            messages.error(self.request, f'Errore durante l\'importazione: {str(e)}')
            return self.form_invalid(form)
    
    def _read_csv(self, file):
        """Read CSV file and return data with cleaned headers"""
        data = []
        decoded_file = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)
        
        # Clean column headers (strip whitespace and remove trailing commas)
        if reader.fieldnames:
            cleaned_fieldnames = [name.strip().rstrip(',').strip() for name in reader.fieldnames]
            reader.fieldnames = cleaned_fieldnames
        
        for row in reader:
            data.append(row)
        
        return data
    
    def _read_excel(self, file):
        """Read Excel file and return data with cleaned headers"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for Excel import. Please install it: pip install pandas openpyxl")
        df = pd.read_excel(file)
        
        # Clean column headers (strip whitespace and remove trailing commas)
        df.columns = [str(col).strip().rstrip(',').strip() for col in df.columns]
        
        return df.to_dict('records')
    
    def _import_interventions(self, interventions_data, overwrite_existing):
        """Import interventions from data"""
        imported_count = 0
        
        for row in interventions_data:
            try:
                # Map column names (handle both Italian and English headers)
                field_mapping = {
                    # Codice NIGIT variations
                    'Codice NIGIT': 'codice_nigit',
                    'Codice NIGIT,': 'codice_nigit',
                    'codice_nigit': 'codice_nigit',
                    # ODA variations
                    'ODA': 'oda',
                    'ODA,': 'oda',
                    'oda': 'oda',
                    # Anno variations
                    'Anno Intervento': 'anno_intervento',
                    'anno_intervento': 'anno_intervento',
                    'ANNO': 'anno_intervento',
                    'ANNO,': 'anno_intervento',
                    # Nome/Intervento variations
                    'INTERVENTO': 'nome',
                    'INTERVENTO,': 'nome',
                    'Nome': 'nome',
                    'nome': 'nome',
                    # Cliente variations
                    'CLIENTE': 'cliente',
                    'CLIENTE,': 'cliente',
                    'Cliente': 'cliente',
                    'cliente': 'cliente',
                    # Assistente variations
                    'Nome Assistente': 'assistente',
                    'Nome Assistente,': 'assistente',
                    'Assistente': 'assistente',
                    'assistente': 'assistente',
                    # Data richiesta variations
                    'Data richiesta': 'data_richiesta',
                    'Data richiesta,': 'data_richiesta',
                    'Data Richiesta': 'data_richiesta',
                    'data_richiesta': 'data_richiesta',
                    # Tipologia variations
                    'Tipologia intervento': 'tipologia_intervento',
                    'Tipologia intervento,': 'tipologia_intervento',
                    'Tipologia Intervento': 'tipologia_intervento',
                    'tipologia_intervento': 'tipologia_intervento',
                    # Ticket variations
                    'Ticket': 'ticket',
                    'Ticket,': 'ticket',
                    'ticket': 'ticket',
                    # International Code variations
                    'INTERNATIONAL CODE': 'international_code',
                    'INTERNATIONAL CODE ,': 'international_code',
                    'International Code': 'international_code',
                    'international_code': 'international_code',
                    # Codice Sito variations
                    'Codice Sito': 'codice_sito',
                    'Codice Sito,': 'codice_sito',
                    'codice_sito': 'codice_sito',
                    # Data Assegnazione Squadra variations
                    'Data Assegnazione Squadra': 'data_assegnazione_squadra',
                    'Data Assegnazione Squadra,': 'data_assegnazione_squadra',
                    'data_assegnazione_squadra': 'data_assegnazione_squadra',
                    # Stato Avanzamento NIGIT variations
                    'Stato Avanzamento NIGIT': 'stato_avanzamento_nigit',
                    'Stato Avanzamento NIGIT,': 'stato_avanzamento_nigit',
                    'stato_avanzamento_nigit': 'stato_avanzamento_nigit',
                    # Stato Avanzamento Contabile variations
                    'Stato avanzamento Contabile NIGIT': 'stato_avanzamento_contabile_nigit',
                    'Stato avanzamento Contabile NIGIT,': 'stato_avanzamento_contabile_nigit',
                    'Stato Avanzamento Contabile NIGIT': 'stato_avanzamento_contabile_nigit',
                    'stato_avanzamento_contabile_nigit': 'stato_avanzamento_contabile_nigit',
                    # Stato Contabile Sirti variations
                    'Stato Contabile Sirti': 'stato_contabile_sirti',
                    'Stato Contabile Sirti ,': 'stato_contabile_sirti',
                    'stato_contabile_sirti': 'stato_contabile_sirti',
                    # Stato Contabile da nigit a Cliente variations
                    'Stato Contabile da nigit a Cliente': 'stato_contabile_da_nigit_a_cliente',
                    'Stato Contabile da nigit a Cliente ,': 'stato_contabile_da_nigit_a_cliente',
                    'Stato Contabile da NIGIT a Cliente': 'stato_contabile_da_nigit_a_cliente',
                    'stato_contabile_da_nigit_a_cliente': 'stato_contabile_da_nigit_a_cliente',
                    # Note variations
                    'Note ,': 'note',
                    'Note': 'note',
                    'note': 'note',
                    # Data Chiusura Lavori variations
                    'Data Chiusura Lavori ,': 'data_chiusura_lavori',
                    'Data Chiusura Lavori': 'data_chiusura_lavori',
                    'data_chiusura_lavori': 'data_chiusura_lavori',
                    # Data Invio Preventivo variations
                    'Data Invio Preventivo ,': 'data_invio_preventivo',
                    'Data Invio Preventivo': 'data_invio_preventivo',
                    'data_invio_preventivo': 'data_invio_preventivo',
                    # Data Approvazione Preventivo variations
                    'Data Approvazione Preventivo': 'data_approvazione_preventivo',
                    'Data Approvazione Preventivo,': 'data_approvazione_preventivo',
                    'data_approvazione_preventivo': 'data_approvazione_preventivo',
                    # TOT Richiesto variations
                    'TOT Richiesto': 'tot_richiesto',
                    'TOT Richiesto,': 'tot_richiesto',
                    'Tot Richiesto': 'tot_richiesto',
                    'tot_richiesto': 'tot_richiesto',
                    # Importo autorizzato Sirti variations
                    'Importo autorizzato Sirti ,': 'importo_autorizzato_sirti',
                    'Importo autorizzato Sirti': 'importo_autorizzato_sirti',
                    'Importo Autorizzato Sirti': 'importo_autorizzato_sirti',
                    'importo_autorizzato_sirti': 'importo_autorizzato_sirti',
                    # Differenza dare/avere variations
                    'Differenza dare/avere': 'differenza_dare_avere',
                    'Differenza dare/avere,': 'differenza_dare_avere',
                    'Differenza Dare/Avere': 'differenza_dare_avere',
                    'differenza_dare_avere': 'differenza_dare_avere',
                    # SES SIRTI variations
                    'SES SIRTI': 'ses_sirti',
                    'SES Sirti': 'ses_sirti',
                    'ses_sirti': 'ses_sirti',
                }
                
                # Map data to model fields (handle duplicate columns)
                intervention_data = {}
                
                # Prioritize specific columns to avoid conflicts
                priority_mapping = {
                    'cliente': ['Cliente', 'CLIENTE', 'cliente', 'CLIENTE,', 'Cliente,'],  # Will check in order and combine
                }
                
                # First handle priority mappings (combine multiple columns)
                for model_field, csv_fields in priority_mapping.items():
                    combined_values = []
                    for csv_field in csv_fields:
                        if csv_field in row and row[csv_field]:
                            value = str(row[csv_field]).strip()
                            if value and value != '-' and value != '':
                                combined_values.append(value)
                    
                    # Combine all non-empty values with space
                    if combined_values:
                        intervention_data[model_field] = ' '.join(combined_values)
                        # DEBUG: Show which columns were used
                        if model_field == 'cliente':
                            print(f"DEBUG: Combined Cliente columns: {combined_values} -> '{intervention_data[model_field]}'")
                
                # Then handle all other mappings
                for csv_field, model_field in field_mapping.items():
                    if model_field in intervention_data:
                        continue  # Skip if already set by priority mapping
                    if csv_field in row and row[csv_field]:
                        value = str(row[csv_field]).strip()
                        # Skip empty values and hyphens
                        if value and value != '-' and value != '':
                            intervention_data[model_field] = value
                
                # DEBUG: Show all mapped data for this row
                if intervention_data.get('codice_nigit'):
                    print(f"DEBUG ROW {imported_count + 1}: Codice NIGIT = {intervention_data.get('codice_nigit')}")
                    print(f"  Mapped fields: {len(intervention_data)}")
                    for field, value in intervention_data.items():
                        if field != 'codice_nigit':
                            print(f"    {field}: {value}")
                    print()
                
                # Handle date fields (support Italian date format DD/MM/YYYY)
                date_fields = [
                    'data_richiesta', 'data_assegnazione_squadra', 'data_chiusura_lavori',
                    'data_invio_preventivo', 'data_approvazione_preventivo'
                ]
                for field in date_fields:
                    if field in intervention_data:
                        try:
                            value = intervention_data[field]
                            if isinstance(value, str):
                                # Skip if value is hyphen or empty
                                if value.strip() in ['-', '', 'None', 'null']:
                                    intervention_data[field] = None
                                    continue
                                # Try Italian date format first (DD/MM/YYYY)
                                try:
                                    intervention_data[field] = timezone.datetime.strptime(
                                        value.strip(), '%d/%m/%Y'
                                    ).date()
                                except ValueError:
                                    # Try standard format (YYYY-MM-DD)
                                    intervention_data[field] = timezone.datetime.strptime(
                                        value.strip(), '%Y-%m-%d'
                                    ).date()
                        except (ValueError, TypeError):
                            intervention_data[field] = None
                
                # Handle numeric fields
                numeric_fields = [
                    'anno_intervento', 'tot_richiesto', 'importo_autorizzato_sirti',
                    'differenza_dare_avere', 'ses_sirti'
                ]
                for field in numeric_fields:
                    if field in intervention_data:
                        try:
                            value = intervention_data[field]
                            if isinstance(value, str):
                                # Skip if value is hyphen or empty
                                if value.strip() in ['-', '', 'None', 'null']:
                                    intervention_data[field] = None
                                    continue
                                # Clean currency values (remove € and ., then replace , with .)
                                if field in ['tot_richiesto', 'importo_autorizzato_sirti', 'differenza_dare_avere', 'ses_sirti']:
                                    value = value.replace('€', '').replace('.', '').replace(',', '.').strip()
                                intervention_data[field] = float(value)
                            if field == 'anno_intervento':
                                intervention_data[field] = int(intervention_data[field])
                        except (ValueError, TypeError):
                            intervention_data[field] = None
                
                # Check if intervention already exists or create new one
                codice_nigit = intervention_data.get('codice_nigit')
                
                if overwrite_existing:
                    if codice_nigit:
                        # Update or create by codice_nigit
                        intervention, created = Intervention.objects.update_or_create(
                            codice_nigit=codice_nigit,
                            defaults=intervention_data
                        )
                    else:
                        # Create new intervention without codice_nigit
                        intervention = Intervention.objects.create(**intervention_data)
                        created = True
                    # DEBUG: Show what happened
                    action = "CREATED" if created else "UPDATED"
                    print(f"DEBUG: {action} intervention {codice_nigit or '(no code)'} with {len(intervention_data)} fields")
                else:
                    if codice_nigit:
                        # Only create if doesn't exist
                        intervention, created = Intervention.objects.get_or_create(
                            codice_nigit=codice_nigit,
                            defaults=intervention_data
                        )
                    else:
                        # Create new intervention without codice_nigit
                        intervention = Intervention.objects.create(**intervention_data)
                        created = True
                    # DEBUG: Show what happened
                    action = "CREATED" if created else "SKIPPED (already exists)"
                    print(f"DEBUG: {action} intervention {codice_nigit or '(no code)'}")
                
                if created or overwrite_existing:
                    imported_count += 1
                        
            except Exception as e:
                # Log error but continue with other records
                print(f"Error importing row: {e}")
                continue
        
        return imported_count


@login_required
def export_interventions_csv(request):
    """
    Export interventions to CSV
    """
    interventions = Intervention.objects.select_related('created_by', 'used_car').prefetch_related('assigned_employees')
    
    # Apply filters if provided
    search_form = InterventionSearchForm(request.GET)
    if search_form.is_valid():
        # Apply same filtering logic as in list view
        search_field = search_form.cleaned_data.get('search_field')
        search_value = search_form.cleaned_data.get('search_value')
        stato_avanzamento = search_form.cleaned_data.get('stato_avanzamento')
        anno_intervento = search_form.cleaned_data.get('anno_intervento')
        cliente_filter = search_form.cleaned_data.get('cliente_filter')
        
        if search_value:
            if search_field:
                filter_kwargs = {f'{search_field}__icontains': search_value}
                interventions = interventions.filter(**filter_kwargs)
            else:
                interventions = interventions.filter(
                    Q(codice_nigit__icontains=search_value) |
                    Q(cliente__icontains=search_value) |
                    Q(nome__icontains=search_value) |
                    Q(assistente__icontains=search_value) |
                    Q(ticket__icontains=search_value) |
                    Q(codice_sito__icontains=search_value) |
                    Q(oda__icontains=search_value)
                )
        
        if stato_avanzamento:
            interventions = interventions.filter(stato_avanzamento_nigit=stato_avanzamento)
        
        if anno_intervento:
            interventions = interventions.filter(anno_intervento=anno_intervento)
        
        if cliente_filter:
            interventions = interventions.filter(cliente__icontains=cliente_filter)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="interventions.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Codice NIGIT', 'ODA', 'Anno Intervento', 'Cliente', 'Nome', 'Assistente',
        'Data Richiesta', 'Tipologia Intervento', 'Ticket', 'International Code',
        'Codice Sito', 'Data Assegnazione Squadra', 'Stato Avanzamento NIGIT',
        'Stato Avanzamento Contabile NIGIT', 'Stato Contabile Sirti',
        'Stato Contabile da NIGIT a Cliente', 'Note', 'Data Chiusura Lavori',
        'Data Invio Preventivo', 'Data Approvazione Preventivo', 'Tot Richiesto',
        'Importo Autorizzato Sirti', 'Differenza Dare/Avere', 'SES Sirti',
        'Creato il', 'Aggiornato il'
    ])
    
    # Write data
    for intervention in interventions:
        writer.writerow([
            intervention.codice_nigit or '',
            intervention.oda or '',
            intervention.anno_intervento or '',
            intervention.cliente or '',
            intervention.nome or '',
            intervention.assistente or '',
            intervention.data_richiesta or '',
            intervention.tipologia_intervento or '',
            intervention.ticket or '',
            intervention.international_code or '',
            intervention.codice_sito or '',
            intervention.data_assegnazione_squadra or '',
            intervention.get_stato_avanzamento_nigit_display() or '',
            intervention.get_stato_avanzamento_contabile_nigit_display() or '',
            intervention.get_stato_contabile_sirti_display() or '',
            intervention.get_stato_contabile_da_nigit_a_cliente_display() or '',
            intervention.note or '',
            intervention.data_chiusura_lavori or '',
            intervention.data_invio_preventivo or '',
            intervention.data_approvazione_preventivo or '',
            intervention.tot_richiesto or '',
            intervention.importo_autorizzato_sirti or '',
            intervention.differenza_dare_avere or '',
            intervention.ses_sirti or '',
            intervention.created_at,
            intervention.updated_at,
        ])
    
    return response


@login_required
def intervention_dashboard(request):
    """
    Dashboard view for interventions with statistics
    """
    # Basic statistics
    total_interventions = Intervention.objects.count()
    interventions_by_status = Intervention.objects.values('stato_avanzamento_nigit').annotate(count=Count('id'))
    total_value = Intervention.objects.aggregate(total=Sum('tot_richiesto'))['total'] or 0
    
    # Recent interventions
    recent_interventions = Intervention.objects.select_related('created_by').order_by('-created_at')[:10]
    
    # Overdue interventions
    overdue_interventions = Intervention.objects.filter(
        data_richiesta__lt=timezone.now().date(),
        stato_avanzamento_nigit__in=['DA_INIZIARE', 'IN_CORSO']
    ).count()
    
    context = {
        'total_interventions': total_interventions,
        'interventions_by_status': interventions_by_status,
        'total_value': total_value,
        'overdue_interventions': overdue_interventions,
        'recent_interventions': recent_interventions,
    }
    
    return render(request, 'interventions/intervention_dashboard.html', context)
