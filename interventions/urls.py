from django.shortcuts import redirect
from django.urls import path, include
from .views import *
from .map_views import sites_map, import_sites_csv, clear_sites_cache
from .intervention_views import (
    InterventionListView, InterventionDetailView, InterventionCreateView,
    InterventionUpdateView, InterventionDeleteView, InterventionImportView, 
    export_interventions_csv, intervention_dashboard, bulk_delete_interventions
)

app_name = 'interventions'

# Redirect old intervention list to new module
def intervention_list_redirect(request):
    return redirect('interventions:intervention-list')

urlpatterns = [
    # New Intervention Module URLs (Class-based views) - MAIN ENTRY POINT
    path('', InterventionListView.as_view(), name='intervention-list'),
    path('create/', InterventionCreateView.as_view(), name='intervention-create'),
    path('<uuid:pk>/', InterventionDetailView.as_view(), name='intervention-detail'),
    path('<uuid:pk>/edit/', InterventionUpdateView.as_view(), name='intervention-update'),
    path('<uuid:pk>/delete/', InterventionDeleteView.as_view(), name='intervention-delete'),
    path('bulk-delete/', bulk_delete_interventions, name='intervention-bulk-delete'),
    path('import/', InterventionImportView.as_view(), name='intervention-import'),
    path('export/csv/', export_interventions_csv, name='intervention-export-csv'),
    path('dashboard/', intervention_dashboard, name='intervention-dashboard'),
    
    # Legacy interventions views (kept for compatibility but redirected)
    path('legacy/', intervention_list_redirect, name='intervention_list'),
    path('legacy/create/', intervention_create, name='intervention_create'),
    path('legacy/<uuid:pk>/', intervention_detail, name='intervention_detail'),
    path('legacy/<uuid:pk>/delete/', intervention_delete, name='intervention_delete'),
    path('legacy/<uuid:pk>/edit/', intervention_edit, name='intervention_edit'),
    
    # Map views
    path('sites-map/', sites_map, name='sites_map'),
    
    # CSV import endpoint
    path('import-sites-csv/', import_sites_csv, name='import_sites_csv'),
    
    # Clear cache endpoint
    path('clear-sites-cache/', clear_sites_cache, name='clear_sites_cache'),
]
