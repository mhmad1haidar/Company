"""
Alternative Storage Methods for Telecom Sites Data
===============================================

This file contains different approaches to store site data persistently.
Choose the method that best fits your requirements.

METHOD 1: JSON File Storage (Simple, File-based)
METHOD 2: Database with File Backup (Hybrid Approach)
METHOD 3: Cache-based Storage (Fast, Temporary)
METHOD 4: Multiple Database Tables (Structured)
METHOD 5: File-based with Versioning (History Tracking)
"""

import json
import os
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from .models import TelecomSite

# ========================================
# METHOD 1: JSON File Storage
# ========================================

def save_sites_to_json_file(sites_data, filename="telecom_sites.json"):
    """
    Save sites data to a JSON file in the project directory
    """
    try:
        file_path = os.path.join(settings.BASE_DIR, filename)
        
        # Add metadata
        data_with_metadata = {
            'timestamp': datetime.now().isoformat(),
            'count': len(sites_data),
            'sites': sites_data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_with_metadata, f, ensure_ascii=False, indent=2)
        
        print(f"SUCCESS: Saved {len(sites_data)} sites to {filename}")
        return True
        
    except Exception as e:
        print(f"Error saving to JSON file: {e}")
        return False

def load_sites_from_json_file(filename="telecom_sites.json"):
    """
    Load sites data from JSON file
    """
    try:
        file_path = os.path.join(settings.BASE_DIR, filename)
        
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sites = data.get('sites', [])
        print(f"SUCCESS: Loaded {len(sites)} sites from {filename}")
        return sites
        
    except Exception as e:
        print(f"Error loading from JSON file: {e}")
        return []

# ========================================
# METHOD 2: Database with File Backup
# ========================================

def save_sites_hybrid(sites_data, request):
    """
    Save to both database and JSON file (maximum reliability)
    """
    success = True
    
    # Save to database
    try:
        TelecomSite.objects.all().delete()
        for site_data in sites_data:
            TelecomSite.objects.create(
                site_name=site_data.get('site_name', ''),
                site_code=site_data.get('site_code', ''),
                area=site_data.get('area', ''),
                region=site_data.get('region', ''),
                province=site_data.get('province', ''),
                city=site_data.get('city', ''),
                address=site_data.get('address', ''),
                latitude=site_data.get('latitude', 0),
                longitude=site_data.get('longitude', 0),
                created_by=request.user
            )
        print("SUCCESS: Saved to database")
    except Exception as e:
        print(f"Database save failed: {e}")
        success = False
    
    # Save to JSON file as backup
    if not save_sites_to_json_file(sites_data):
        success = False
    
    return success

def load_sites_hybrid():
    """
    Load from database first, fallback to JSON file
    """
    try:
        # Try database first
        sites = list(TelecomSite.objects.all().values(
            'site_name', 'site_code', 'area', 'region', 'province', 
            'city', 'address', 'latitude', 'longitude'
        ))
        
        if sites:
            # Convert Decimal to float
            for site in sites:
                if 'latitude' in site and site['latitude'] is not None:
                    site['latitude'] = float(site['latitude'])
                if 'longitude' in site and site['longitude'] is not None:
                    site['longitude'] = float(site['longitude'])
            
            print(f"SUCCESS: Loaded {len(sites)} sites from database")
            return sites
    except Exception as e:
        print(f"Database load failed: {e}")
    
    # Fallback to JSON file
    return load_sites_from_json_file()

# ========================================
# METHOD 3: Cache-based Storage
# ========================================

def save_sites_to_cache(sites_data, timeout=3600):
    """
    Save sites to Django cache (fast, but temporary)
    """
    try:
        cache.set('telecom_sites', sites_data, timeout)
        cache.set('telecom_sites_timestamp', datetime.now().isoformat(), timeout)
        print(f"SUCCESS: Saved {len(sites_data)} sites to cache")
        return True
    except Exception as e:
        print(f"Cache save failed: {e}")
        return False

def load_sites_from_cache():
    """
    Load sites from Django cache
    """
    try:
        sites = cache.get('telecom_sites')
        if sites:
            timestamp = cache.get('telecom_sites_timestamp')
            print(f"SUCCESS: Loaded {len(sites)} sites from cache (saved: {timestamp})")
            return sites
        else:
            print("No sites in cache")
            return []
    except Exception as e:
        print(f"Cache load failed: {e}")
        return []

# ========================================
# METHOD 4: Multiple Database Tables (Structured)
# ========================================

def save_sites_structured(sites_data, request):
    """
    Save sites to multiple related tables for better structure
    """
    try:
        from .models import TelecomSite, Region, Province, City
        
        # Clear existing data
        TelecomSite.objects.all().delete()
        
        for site_data in sites_data:
            # Get or create region
            region, _ = Region.objects.get_or_create(
                name=site_data.get('region', ''),
                defaults={'code': site_data.get('region', '')[:10]}
            )
            
            # Get or create province
            province, _ = Province.objects.get_or_create(
                name=site_data.get('province', ''),
                region=region,
                defaults={'code': site_data.get('province', '')[:10]}
            )
            
            # Get or create city
            city, _ = City.objects.get_or_create(
                name=site_data.get('city', ''),
                province=province,
                defaults={'code': site_data.get('city', '')[:10]}
            )
            
            # Create site
            TelecomSite.objects.create(
                site_name=site_data.get('site_name', ''),
                site_code=site_data.get('site_code', ''),
                area=site_data.get('area', ''),
                region=region,
                province=province,
                city=city,
                address=site_data.get('address', ''),
                latitude=site_data.get('latitude', 0),
                longitude=site_data.get('longitude', 0),
                created_by=request.user
            )
        
        print(f"SUCCESS: Saved {len(sites_data)} sites to structured database")
        return True
        
    except Exception as e:
        print(f"Structured save failed: {e}")
        return False

# ========================================
# METHOD 5: File-based with Versioning
# ========================================

def save_sites_versioned(sites_data, request):
    """
    Save sites with version history
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"telecom_sites_v{timestamp}.json"
        
        # Save current version
        save_sites_to_json_file(sites_data, filename)
        
        # Update latest version symlink (or copy)
        latest_file = os.path.join(settings.BASE_DIR, "telecom_sites_latest.json")
        current_file = os.path.join(settings.BASE_DIR, filename)
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'version': timestamp,
                'count': len(sites_data),
                'sites': sites_data
            }, f, ensure_ascii=False, indent=2)
        
        print(f"SUCCESS: Saved version {timestamp} with {len(sites_data)} sites")
        return True
        
    except Exception as e:
        print(f"Versioned save failed: {e}")
        return False

def load_sites_versioned():
    """
    Load latest version of sites
    """
    return load_sites_from_json_file("telecom_sites_latest.json")

# ========================================
# USAGE EXAMPLES
# ========================================

def example_usage():
    """
    Examples of how to use different storage methods
    """
    # Sample sites data
    sites_data = [
        {
            'site_name': 'Test Site 1',
            'site_code': 'TS001',
            'address': '123 Test Street',
            'latitude': 45.0,
            'longitude': 7.0
        }
    ]
    
    print("=== Storage Method Examples ===")
    
    # Method 1: JSON File
    print("\n1. JSON File Storage:")
    save_sites_to_json_file(sites_data)
    loaded = load_sites_from_json_file()
    
    # Method 2: Hybrid
    print("\n2. Hybrid Storage:")
    # save_sites_hybrid(sites_data, request)  # Needs request object
    # loaded = load_sites_hybrid()
    
    # Method 3: Cache
    print("\n3. Cache Storage:")
    save_sites_to_cache(sites_data)
    loaded = load_sites_from_cache()
    
    # Method 5: Versioned
    print("\n5. Versioned Storage:")
    # save_sites_versioned(sites_data, request)  # Needs request object
    # loaded = load_sites_versioned()

if __name__ == '__main__':
    example_usage()
