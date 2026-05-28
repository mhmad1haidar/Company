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
    path('items/<int:item_id>/quick-stock/', views.update_item_stock_inline, name='update_item_stock_inline'),
    path('items/<int:item_id>/add-supplier/', views.AddItemSupplierView.as_view(), name='add_item_supplier'),
    path('supplier/<int:pk>/edit/', views.EditItemSupplierView.as_view(), name='edit_item_supplier'),
    path('supplier/<int:pk>/delete/', views.delete_item_supplier, name='delete_item_supplier'),
    path('create-supplier/', views.create_supplier_ajax, name='create_supplier_ajax'),
    path('items/<int:item_id>/barcode/', views.generate_barcode_image, name='barcode_image'),
    path('items/<int:item_id>/qr/', views.generate_qr_code, name='qr_code'),
    path('items/print-labels/', views.print_barcode_labels, name='print_labels'),
    path('report/inventory/', views.inventory_report, name='inventory_report'),
    path('items/export/', views.export_items_csv, name='export_items'),
    path('items/bulk-delete/', views.bulk_delete_items, name='bulk_delete_items'),
    path('items/bulk-update/', views.bulk_update_items, name='bulk_update_items'),
    path('items/<int:item_id>/generate-barcode/', views.generate_barcode, name='generate_barcode'),
    path('items/<int:item_id>/generate-qr/', views.generate_qr_code_pdf, name='generate_qr_code_pdf'),
    path('report/inventory/pdf/', views.export_inventory_pdf, name='export_inventory_pdf'),
    path('report/inventory/csv/', views.export_inventory_csv, name='export_inventory_csv'),
    path('report/inventory/excel/', views.export_inventory_excel, name='export_inventory_excel'),
    
    # Purchase Orders
    path('purchase-orders/', views.PurchaseOrderListView.as_view(), name='purchase_order_list'),
    path('purchase-orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('purchase-orders/add/', views.PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    path('purchase-orders/<int:pk>/edit/', views.PurchaseOrderUpdateView.as_view(), name='purchase_order_update'),
    
    # Batches
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),
    path('batches/add/', views.BatchCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/edit/', views.BatchUpdateView.as_view(), name='batch_update'),
    
    # Stock Movements
    path('movements/', views.StockMovementListView.as_view(), name='movement_list'),
    path('movements/add/', views.StockMovementCreateView.as_view(), name='movement_create'),
    
    # Requests
    path('requests/', views.WarehouseRequestListView.as_view(), name='request_list'),
    path('requests/add/', views.WarehouseRequestCreateView.as_view(), name='request_create'),
    path('requests/<int:pk>/approve/', views.approve_request, name='approve_request'),
    path('requests/<int:pk>/reject/', views.reject_request, name='reject_request'),
    
    # Assignments
    path('assignments/', views.UserAssignmentsListView.as_view(), name='assignments_list'),
    path('assignments/export-overview/<str:file_format>/', views.export_assignment_overview, name='export_assignment_overview'),
    path('assignments/export/', views.export_assignments_csv, name='export_assignments'),
    path('assignments/export/<str:file_format>/', views.export_assignments, name='export_assignments_format'),
    path('serials/<int:pk>/assign/', views.assign_serial, name='assign_serial'),
    path('serials/<int:pk>/unassign/', views.unassign_serial, name='unassign_serial'),
    path('serials/export/', views.export_serial_numbers_csv, name='export_serials'),
    path('serials/export/<str:file_format>/', views.export_serial_numbers, name='export_serials_format'),
    
    # Audit Logs
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit_log_list'),
]
