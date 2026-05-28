from django.contrib import admin
from .models import Category, Supplier, Item, StockMovement, WarehouseRequest, WarehouseRequestItem, ItemSupplier, AuditLog, WarehouseZone, Batch, Stocktaking, StocktakingItem, PurchaseOrder, PurchaseOrderItem, SupplierPerformance, ItemAssignment, SerialNumber


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name", "description")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "email", "phone")
    search_fields = ("name", "contact_person", "email", "phone")


@admin.register(ItemSupplier)
class ItemSupplierAdmin(admin.ModelAdmin):
    list_display = ("item", "supplier", "supplier_code", "unit_price", "is_preferred", "lead_time_days")
    list_filter = ("is_preferred", "supplier", "item__category")
    search_fields = ("item__code", "item__name", "supplier__name", "supplier_code")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "code", "name", "category", "unit_of_measure",
        "quantity", "incoming_quantity", "used_quantity", "in_transit_quantity",
        "status", "location",
    )
    list_filter = ("status", "category")
    search_fields = ("code", "name", "description", "location", "notes")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("item", "movement_type", "quantity", "previous_quantity", "new_quantity", "created_by", "created_at")
    list_filter = ("movement_type", "created_at")
    search_fields = ("item__code", "item__name", "reason", "notes")


@admin.register(WarehouseRequest)
class WarehouseRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "requester", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("requester__username", "reason")
    readonly_fields = ("created_at", "updated_at")


@admin.register(WarehouseRequestItem)
class WarehouseRequestItemAdmin(admin.ModelAdmin):
    list_display = ("request", "item", "quantity_requested", "quantity_approved")
    list_filter = ("request__status", "item__category")
    search_fields = ("item__code", "item__name")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("item", "user", "action", "field_name", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("item__code", "item__name", "user__username")
    readonly_fields = ("created_at",)


@admin.register(WarehouseZone)
class WarehouseZoneAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "created_at")
    search_fields = ("code", "name")


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("item", "batch_number", "quantity", "expiration_date", "supplier")
    list_filter = ("expiration_date", "supplier")
    search_fields = ("item__code", "item__name", "batch_number")


@admin.register(Stocktaking)
class StocktakingAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "conducted_by", "conducted_at", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "description")


@admin.register(StocktakingItem)
class StocktakingItemAdmin(admin.ModelAdmin):
    list_display = ("stocktaking", "item", "expected_quantity", "counted_quantity", "variance")
    list_filter = ("stocktaking",)
    search_fields = ("item__code", "item__name")


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "supplier", "status", "order_date", "expected_delivery_date", "created_by")
    list_filter = ("status", "order_date", "supplier")
    search_fields = ("order_number", "supplier__name")


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ("purchase_order", "item", "quantity_ordered", "quantity_received", "unit_price")
    list_filter = ("purchase_order",)
    search_fields = ("item__code", "item__name")


@admin.register(SupplierPerformance)
class SupplierPerformanceAdmin(admin.ModelAdmin):
    list_display = ("supplier", "total_orders", "on_time_deliveries", "late_deliveries", "rating", "updated_at")
    list_filter = ("rating", "updated_at")
    search_fields = ("supplier__name", "notes")
    readonly_fields = ("on_time_percentage",)


@admin.register(ItemAssignment)
class ItemAssignmentAdmin(admin.ModelAdmin):
    list_display = ("item", "user", "quantity_assigned", "assigned_by", "created_at")
    list_filter = ("item__category", "created_at")
    search_fields = ("item__code", "item__name", "user__username")


@admin.register(SerialNumber)
class SerialNumberAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "item", "status", "assigned_to", "created_at")
    list_filter = ("status", "item__category", "created_at")
    search_fields = ("serial_number", "item__code", "item__name")
