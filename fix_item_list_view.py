with open('c:/Users/assis/company/warehouse/views.py', 'r') as f:
    content = f.read()

# Find and replace the ItemListView get_queryset method
old_code = '''    def get_queryset(self):
        queryset = list(Item.objects.select_related('category').prefetch_related('supplier_details__supplier').all())
        
        # Calculate quantities from stock movements
        for item in queryset:
            item.quantity = item.calculate_quantity()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter('''

new_code = '''    def get_queryset(self):
        queryset = Item.objects.select_related('category').prefetch_related('supplier_details__supplier').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter('''

content = content.replace(old_code, new_code)

# Add the quantity calculation at the end
old_end = '''return queryset.order_by('code', 'name')'''
new_end = '''# Calculate quantities from stock movements
        items_list = list(queryset)
        for item in items_list:
            item.quantity = item.calculate_quantity()
        return items_list'''

content = content.replace(old_end, new_end)

with open('c:/Users/assis/company/warehouse/views.py', 'w') as f:
    f.write(content)

print("Fixed ItemListView")
