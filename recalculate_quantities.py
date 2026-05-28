import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'company.settings')
django.setup()

from warehouse.models import Item

# Recalculate all item quantities from stock movements
items = Item.objects.all()
for item in items:
    calculated = item.calculate_quantity()
    if item.quantity != calculated:
        print(f"Item {item.code}: {item.quantity} -> {calculated}")
        item.quantity = calculated
        item.save()
    else:
        print(f"Item {item.code}: OK ({calculated})")

print("Done recalculating quantities")
