from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, F
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone

from .models import Item, Category, Supplier, StockMovement, WarehouseRequest


class WarehouseDashboardView(LoginRequiredMixin, ListView):
    """Main warehouse dashboard"""
    model = Item
    template_name = 'warehouse/dashboard.html'
    context_object_name = 'items'

    def get_queryset(self):
        return Item.objects.filter(status='active')[:10]  # Show recent items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Dashboard statistics
        context.update({
            'total_items': Item.objects.count(),
            'active_items': Item.objects.filter(status='active').count(),
            'low_stock_items': Item.objects.filter(quantity__lte=F('min_quantity')).count(),
            'out_of_stock_items': Item.objects.filter(quantity=0).count(),
            'pending_requests': WarehouseRequest.objects.filter(status='pending').count(),
            'total_categories': Category.objects.count(),
            'total_suppliers': Supplier.objects.count(),
            
            # Recent stock movements
            'recent_movements': StockMovement.objects.select_related('item', 'created_by')[:5],
            
            # Low stock items
            'low_stock_items_list': Item.objects.filter(quantity__lte=F('min_quantity')).order_by('quantity')[:5],
            
            # Pending requests
            'pending_requests_list': WarehouseRequest.objects.select_related('requester', 'item').filter(status='pending')[:5],
        })
        return context


class ItemListView(LoginRequiredMixin, ListView):
    """List all warehouse items"""
    model = Item
    template_name = 'warehouse/item_list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        queryset = Item.objects.select_related('category', 'supplier').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by stock status
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'low_stock':
            queryset = queryset.filter(quantity__lte=F('min_quantity'))
        elif stock_status == 'out_of_stock':
            queryset = queryset.filter(quantity=0)
        elif stock_status == 'in_stock':
            queryset = queryset.filter(quantity__gt=F('min_quantity'))
        
        return queryset.order_by('code', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'categories': Category.objects.all(),
            'status_choices': Item.STATUS_CHOICES,
        })
        return context


class ItemDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a specific item"""
    model = Item
    template_name = 'warehouse/item_detail.html'
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = self.get_object()
        
        context.update({
            'stock_movements': StockMovement.objects.filter(item=item).select_related('created_by')[:20],
            'related_requests': WarehouseRequest.objects.filter(item=item).select_related('requester')[:10],
        })
        return context


class ItemCreateView(LoginRequiredMixin, CreateView):
    """Create a new warehouse item"""
    model = Item
    template_name = 'warehouse/item_form.html'
    fields = ['code', 'name', 'description', 'category', 'supplier', 'quantity', 'min_quantity', 
              'max_quantity', 'unit_price', 'selling_price', 'status', 'location']
    success_url = reverse_lazy('warehouse:item_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'Item "{form.instance.name}" has been created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'categories': Category.objects.all(),
            'suppliers': Supplier.objects.all(),
            'title': 'Add New Item',
        })
        return context


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing warehouse item"""
    model = Item
    template_name = 'warehouse/item_form.html'
    fields = ['code', 'name', 'description', 'category', 'supplier', 'quantity', 'min_quantity', 
              'max_quantity', 'unit_price', 'selling_price', 'status', 'location']
    success_url = reverse_lazy('warehouse:item_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        
        # Check if quantity changed and create stock movement
        if 'quantity' in form.changed_data:
            old_quantity = Item.objects.get(pk=self.object.pk).quantity
            new_quantity = form.cleaned_data['quantity']
            
            StockMovement.objects.create(
                item=self.object,
                movement_type='adjustment',
                quantity=new_quantity - old_quantity,
                previous_quantity=old_quantity,
                new_quantity=new_quantity,
                reason='Manual adjustment',
                created_by=self.request.user
            )
        
        messages.success(self.request, f'Item "{form.instance.name}" has been updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'categories': Category.objects.all(),
            'suppliers': Supplier.objects.all(),
            'title': 'Edit Item',
        })
        return context


class StockMovementListView(LoginRequiredMixin, ListView):
    """List all stock movements"""
    model = StockMovement
    template_name = 'warehouse/stock_movement_list.html'
    context_object_name = 'movements'
    paginate_by = 30

    def get_queryset(self):
        queryset = StockMovement.objects.select_related('item', 'created_by').all()
        
        # Filter by item
        item_id = self.request.GET.get('item')
        if item_id:
            queryset = queryset.filter(item_id=item_id)
        
        # Filter by movement type
        movement_type = self.request.GET.get('movement_type')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'items': Item.objects.all(),
            'movement_types': StockMovement.MOVEMENT_TYPES,
        })
        return context


class WarehouseRequestListView(LoginRequiredMixin, ListView):
    """List warehouse requests"""
    model = WarehouseRequest
    template_name = 'warehouse/request_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        queryset = WarehouseRequest.objects.select_related('requester', 'item').all()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by requester (for non-admin users)
        if not self.request.user.is_staff:
            queryset = queryset.filter(requester=self.request.user)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'status_choices': WarehouseRequest.STATUS_CHOICES,
        })
        return context


@login_required
def approve_request(request, pk):
    """Approve a warehouse request"""
    warehouse_request = get_object_or_404(WarehouseRequest, pk=pk)
    
    if request.method == 'POST':
        quantity_approved = int(request.POST.get('quantity_approved', 0))
        
        if quantity_approved > 0 and warehouse_request.item.quantity >= quantity_approved:
            warehouse_request.status = 'approved'
            warehouse_request.quantity_approved = quantity_approved
            warehouse_request.approved_by = request.user
            warehouse_request.approved_at = timezone.now()
            warehouse_request.save()
            
            # Create stock movement
            StockMovement.objects.create(
                item=warehouse_request.item,
                movement_type='out',
                quantity=-quantity_approved,
                previous_quantity=warehouse_request.item.quantity,
                new_quantity=warehouse_request.item.quantity - quantity_approved,
                reason=f'Approved request #{warehouse_request.id}',
                created_by=request.user
            )
            
            # Update item quantity
            warehouse_request.item.quantity -= quantity_approved
            warehouse_request.item.save()
            
            messages.success(request, 'Request approved successfully.')
        else:
            messages.error(request, 'Invalid quantity or insufficient stock.')
    
    return redirect('warehouse:request_list')


@login_required
def reject_request(request, pk):
    """Reject a warehouse request"""
    warehouse_request = get_object_or_404(WarehouseRequest, pk=pk)
    
    if request.method == 'POST':
        warehouse_request.status = 'rejected'
        warehouse_request.approved_by = request.user
        warehouse_request.approved_at = timezone.now()
        warehouse_request.save()
        
        messages.success(request, 'Request rejected successfully.')
    
    return redirect('warehouse:request_list')
