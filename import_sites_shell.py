import os
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'company.settings')

import django
django.setup()

from interventions.models import TelecomSite
from accounts.models import User

# Load JSON file
json_file_path = 'telecom_sites.json'
with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

sites_data = data.get('sites', [])
print(f'Found {len(sites_data)} sites in JSON file')

# Get or create a user for created_by
user = User.objects.filter(is_superuser=True).first()
if not user:
    user = User.objects.first()

imported_count = 0
updated_count = 0

for site_data in sites_data:
    site_code = site_data.get('site_code', '')
    
    # Check if site already exists
    existing_site = TelecomSite.objects.filter(site_code=site_code).first()
    
    if existing_site:
        # Update existing site
        existing_site.site_name = site_data.get('site_name', existing_site.site_name)
        existing_site.area = site_data.get('area', existing_site.area)
        existing_site.region = site_data.get('region', existing_site.region)
        existing_site.province = site_data.get('province', existing_site.province)
        existing_site.city = site_data.get('city', existing_site.city)
        existing_site.address = site_data.get('address', existing_site.address)
        existing_site.latitude = float(site_data.get('latitude', existing_site.latitude))
        existing_site.longitude = float(site_data.get('longitude', existing_site.longitude))
        existing_site.save()
        updated_count += 1
    else:
        # Create new site
        TelecomSite.objects.create(
            site_name=site_data.get('site_name', ''),
            site_code=site_code,
            area=site_data.get('area', ''),
            region=site_data.get('region', ''),
            province=site_data.get('province', ''),
            city=site_data.get('city', ''),
            address=site_data.get('address', ''),
            latitude=float(site_data.get('latitude', 0)),
            longitude=float(site_data.get('longitude', 0)),
            created_by=user
        )
        imported_count += 1

print(f'Import complete: {imported_count} new sites, {updated_count} updated sites')
print(f'Total sites in database: {TelecomSite.objects.count()}')
