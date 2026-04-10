from django.urls import path
from . import intervention_views

app_name = 'interventions'

urlpatterns = [
    # Intervention CRUD
    path('', intervention_views.InterventionListView.as_view(), name='intervention-list'),
    path('intervention/<uuid:pk>/', intervention_views.InterventionDetailView.as_view(), name='intervention-detail'),
    path('intervention/create/', intervention_views.InterventionCreateView.as_view(), name='intervention-create'),
    path('intervention/<uuid:pk>/edit/', intervention_views.InterventionUpdateView.as_view(), name='intervention-update'),
    path('intervention/<uuid:pk>/delete/', intervention_views.InterventionDeleteView.as_view(), name='intervention-delete'),
    path('bulk-delete/', intervention_views.bulk_delete_interventions, name='intervention-bulk-delete'),
    
    # Import/Export
    path('import/', intervention_views.InterventionImportView.as_view(), name='intervention-import'),
    path('export/csv/', intervention_views.export_interventions_csv, name='intervention-export-csv'),
    
    # Dashboard
    path('dashboard/', intervention_views.intervention_dashboard, name='intervention-dashboard'),
]
