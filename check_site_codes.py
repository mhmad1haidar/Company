import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'company.settings')
django.setup()

from interventions.models import TelecomSite

print("=== First 10 TelecomSite records ===")
sites = TelecomSite.objects.all()[:10]
for s in sites:
    print(f"site_code='{s.site_code}', site_name='{s.site_name}', lat={s.latitude}, lng={s.longitude}")

print("\n=== All unique site_code values ===")
unique_codes = TelecomSite.objects.values_list('site_code', flat=True).distinct()
print(f"Total unique site_code values: {len([c for c in unique_codes if c])}")
for code in unique_codes[:20]:
    if code:
        print(f"  '{code}'")
