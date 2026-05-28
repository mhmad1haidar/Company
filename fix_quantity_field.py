with open('c:/Users/assis/company/warehouse/views.py', 'r') as f:
    content = f.read()

# Remove quantity from ItemCreateView fields (around line 158)
content = content.replace(
    "fields = ['code', 'name', 'description', 'category', 'barcode', 'zone', 'image',\n              'quantity', 'incoming_quantity', 'used_quantity', 'in_transit_quantity',",
    "fields = ['code', 'name', 'description', 'category', 'barcode', 'zone', 'image',\n              'incoming_quantity', 'used_quantity', 'in_transit_quantity',"
)

# Remove quantity from ItemUpdateView fields (around line 244)
content = content.replace(
    "fields = ['code', 'name', 'description', 'category', 'barcode', 'zone', 'image',\n              'quantity', 'incoming_quantity', 'used_quantity', 'in_transit_quantity',",
    "fields = ['code', 'name', 'description', 'category', 'barcode', 'zone', 'image',\n              'incoming_quantity', 'used_quantity', 'in_transit_quantity',"
)

with open('c:/Users/assis/company/warehouse/views.py', 'w') as f:
    f.write(content)

print("Removed quantity from editable fields")
