import os
import sys
import django

sys.path.insert(0, 'c:/Users/assis/company')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'company.settings')
django.setup()

from interventions.models import TelecomSite, Intervention

print("=== TelecomSite Examples ===")
sites = TelecomSite.objects.all()[:5]
for s in sites:
    print(f"site_code='{s.site_code}', name='{s.site_name}', lat={s.latitude}, lng={s.longitude}")

print("\n=== Intervention Examples ===")
interventions = Intervention.objects.filter(international_code__isnull=False)[:5]
for i in interventions:
    print(f"international_code='{i.international_code}', codice_sito='{i.codice_sito}', nome='{i.nome}'")
