from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    # Assignment CRUD
    path('', views.WorkAssignmentListView.as_view(), name='assignment-list'),
    path('assignment/<uuid:pk>/', views.WorkAssignmentDetailView.as_view(), name='assignment-detail'),
    path('assignment/create/', views.WorkAssignmentCreateView.as_view(), name='assignment-create'),
    path('assignment/<uuid:pk>/edit/', views.WorkAssignmentUpdateView.as_view(), name='assignment-update'),
    
    # My assignments
    path('my-assignments/', views.my_assignments, name='my-assignments'),
    
    # Create from intervention
    path('create-from-intervention/<uuid:intervention_id>/', views.create_assignment_from_intervention, name='create-from-intervention'),
    
    # AJAX actions
    path('assignment/<uuid:pk>/update-status/', views.update_assignment_status, name='update-status'),
    path('assignment/<uuid:pk>/update-work-status/', views.update_work_status, name='update-work-status'),
    path('assignment/<uuid:pk>/complete/', views.complete_assignment, name='complete-assignment'),
    path('assignment/<uuid:pk>/delete/', views.delete_assignment, name='delete-assignment'),
]
