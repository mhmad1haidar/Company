from django.urls import path
from . import views

app_name = "warehouse"

urlpatterns = [
    # Dashboard
    path('', views.WarehouseDashboardView.as_view(), name='dashboard'),
    
    # Items
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('items/add/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item_update'),
    
    # Stock Movements
    path('movements/', views.StockMovementListView.as_view(), name='movement_list'),
    
    # Requests
    path('requests/', views.WarehouseRequestListView.as_view(), name='request_list'),
    path('requests/<int:pk>/approve/', views.approve_request, name='approve_request'),
    path('requests/<int:pk>/reject/', views.reject_request, name='reject_request'),
]
