from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Category(models.Model):
    """Product categories for warehouse items"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    """Suppliers for warehouse items"""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"

    def __str__(self):
        return self.name

class ItemSupplier(models.Model):
    """Links one Item to one or more Suppliers.

    Each supplier can have its own price (unit_price), its own internal code (SKU),
    description, lead time, minimum order quantity, etc.

    This solves the requirement:
      "the same item can come from multiple suppliers,
       and every supplier has his own price and description".
    """
    item = models.ForeignKey('Item', on_delete=models.CASCADE, related_name='supplier_details')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='item_suppliers')

    # Per-supplier pricing and identification
    supplier_code = models.CharField(
        max_length=100, blank=True,
        help_text="This supplier's own SKU / part number for the item"
    )
    description = models.TextField(
        blank=True,
        help_text="This supplier's description or specifications for the item"
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Purchase / cost price from THIS supplier (different suppliers can have different prices)"
    )

    # Relationship metadata
    is_preferred = models.BooleanField(
        default=False,
        help_text="Mark as the default/preferred supplier when buying this item"
    )
    lead_time_days = models.PositiveIntegerField(
        default=0,
        help_text="Typical number of days from order to delivery from this supplier"
    )
    min_order_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Smallest quantity this supplier is willing to sell"
    )
    notes = models.TextField(
        blank=True,
        help_text="Any special terms, discounts, contracts, or ordering notes for this supplier"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('item', 'supplier')   # One record per supplier per item
        ordering = ['-is_preferred', 'supplier__name']
        verbose_name = "Item Supplier"
        verbose_name_plural = "Item Suppliers"

    def __str__(self):
        return f"{self.item.code} ← {self.supplier.name} @ {self.unit_price}"


class AuditLog(models.Model):
    """Track all changes to warehouse items for accountability"""
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
    ]
    
    item = models.ForeignKey('Item', on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='warehouse_audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    field_name = models.CharField(max_length=100, blank=True, help_text="Field that was changed")
    old_value = models.TextField(blank=True, help_text="Previous value")
    new_value = models.TextField(blank=True, help_text="New value")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
    
    def __str__(self):
        return f"{self.user} {self.action} {self.item} at {self.created_at}"


class WarehouseZone(models.Model):
    """Warehouse zones for organizing inventory"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['code']
        verbose_name = "Warehouse Zone"
        verbose_name_plural = "Warehouse Zones"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Batch(models.Model):
    """Track batches/lots for expiration tracking"""
    item = models.ForeignKey('Item', on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100)
    quantity = models.IntegerField(default=0)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-expiration_date']
        verbose_name = "Batch"
        verbose_name_plural = "Batches"
        unique_together = ('item', 'batch_number')
    
    def __str__(self):
        return f"{self.item.code} - {self.batch_number}"


class Stocktaking(models.Model):
    """Inventory count audits"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    conducted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stocktakings')
    conducted_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Stocktaking"
        verbose_name_plural = "Stocktakings"
    
    def __str__(self):
        return f"{self.name} - {self.status}"


class StocktakingItem(models.Model):
    """Items counted during stocktaking"""
    stocktaking = models.ForeignKey(Stocktaking, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    expected_quantity = models.IntegerField(default=0)
    counted_quantity = models.IntegerField(default=0)
    variance = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['item__code']
        verbose_name = "Stocktaking Item"
        verbose_name_plural = "Stocktaking Items"
    
    def __str__(self):
        return f"{self.item.code}: {self.counted_quantity}"


class PurchaseOrder(models.Model):
    """Track orders to suppliers"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('confirmed', 'Confirmed'),
        ('partial', 'Partially Received'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    order_date = models.DateField(auto_now_add=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
    
    def __str__(self):
        return f"PO-{self.order_number}"


class PurchaseOrderItem(models.Model):
    """Items in a purchase order"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('Item', on_delete=models.PROTECT)
    item_supplier = models.ForeignKey(ItemSupplier, on_delete=models.SET_NULL, null=True, blank=True)
    quantity_ordered = models.IntegerField(default=0)
    quantity_received = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['item__code']
        verbose_name = "Purchase Order Item"
        verbose_name_plural = "Purchase Order Items"
    
    def __str__(self):
        return f"{self.item.code} - {self.quantity_ordered}"


class SupplierPerformance(models.Model):
    """Track supplier performance metrics"""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='performance')
    total_orders = models.IntegerField(default=0)
    on_time_deliveries = models.IntegerField(default=0)
    late_deliveries = models.IntegerField(default=0)
    quality_issues = models.IntegerField(default=0)
    average_lead_time = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Average lead time in days")
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_order_date = models.DateField(null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="Rating from 0 to 5")
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Supplier Performance"
        verbose_name_plural = "Supplier Performances"
        unique_together = ('supplier',)
    
    def __str__(self):
        return f"{self.supplier.name} - {self.rating}/5"
    
    @property
    def on_time_percentage(self):
        if self.total_orders == 0:
            return 0
        return (self.on_time_deliveries / self.total_orders) * 100


class Item(models.Model):
    """Warehouse items/inventory"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
        ('out_of_stock', 'Out of Stock'),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    barcode = models.CharField(max_length=50, blank=True, help_text="Barcode/QR code for scanning")
    zone = models.ForeignKey(WarehouseZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    image = models.ImageField(upload_to='warehouse/items/', blank=True, null=True)
    
    # Stock information (calculated from stock movements - DO NOT EDIT)
    quantity = models.IntegerField(default=0, editable=False)  # Calculated from movements
    incoming_quantity = models.IntegerField(default=0)
    used_quantity = models.IntegerField(default=0)
    in_transit_quantity = models.IntegerField(default=0)
    min_quantity = models.IntegerField(default=0)  # Minimum stock level
    max_quantity = models.IntegerField(default=0)  # Maximum stock level
    unit_of_measure = models.CharField(max_length=30, blank=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    low_stock_alert = models.BooleanField(default=True, help_text="Send email alert when stock falls below minimum")
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    location = models.CharField(max_length=100, blank=True)  # Warehouse location/aisle
    position_area = models.CharField(max_length=100, blank=True)
    position_shelf = models.CharField(max_length=100, blank=True)
    position_level = models.CharField(max_length=100, blank=True)
    position_detail = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='warehouse_items_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='warehouse_items_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def calculate_quantity(self):
        """Calculate quantity from incoming and used quantities"""
        return self.incoming_quantity - self.used_quantity
    
    @property
    def is_low_stock(self):
        """Check if item is below minimum stock level"""
        return self.quantity <= self.min_quantity

    @property
    def stock_status(self):
        """Get stock status indicator"""
        if self.quantity == 0:
            return "Out of Stock"
        elif self.is_low_stock:
            return "Low Stock"
        else:
            return "In Stock"


class StockMovement(models.Model):
    """Track stock movements (in/out)"""
    MOVEMENT_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
        ('transfer', 'Transfer'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()  # Positive for in, negative for out
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    
    reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.item.code} - {self.get_movement_type_display()} ({self.quantity})"


class WarehouseRequest(models.Model):
    """Requests for warehouse items"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='warehouse_requests')
    
    reason = models.TextField()
    notes = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Approval tracking
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Request #{self.id} - {self.get_status_display()}"


class WarehouseRequestItem(models.Model):
    """Items in a warehouse request"""
    request = models.ForeignKey(WarehouseRequest, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity_requested = models.IntegerField()
    quantity_approved = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.item.code} - {self.quantity_requested}"
    
    # Completion tracking
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_requests')
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Request #{self.id} - {self.item.name}"


class ItemAssignment(models.Model):
    """Track item allocations to users"""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='item_assignments')
    quantity_assigned = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments_made')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['item', 'user']

    def __str__(self):
        return f"{self.item.code} - {self.user.username}: {self.quantity_assigned}"


class SerialNumber(models.Model):
    """Track individual serialized items"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('in_use', 'In Use'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
        ('maintenance', 'Maintenance'),
    ]
    
    serial_number = models.CharField(max_length=100, unique=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='serial_numbers')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_serials')
    assigned_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.serial_number} - {self.item.code} ({self.get_status_display()})"
