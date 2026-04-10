import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import csv
import io
from accounts.permissions import get_user_role
from django.core.cache import cache
from .models import TelecomSite
from .storage_methods import save_sites_hybrid, load_sites_hybrid

@login_required
def sites_map(request):
    """
    Map view for telecom sites with clickable markers
    """
    # Use Django's built-in admin checks
    is_admin = request.user.is_superuser or request.user.is_staff
    
    # Debug: Check session data
    session_sites = request.session.get('imported_sites', [])
    print(f"DEBUG: Session has {len(session_sites)} sites")
    
    # Try multiple storage methods for maximum reliability
    sites = []
    
    # Method 1: Try hybrid storage first
    try:
        sites = load_sites_hybrid()
        print(f"DEBUG: Loaded {len(sites)} sites using hybrid storage")
    except Exception as e:
        print(f"DEBUG: Hybrid storage failed: {e}")
    
    # Method 2: Fallback to direct database query
    if not sites:
        try:
            sites = list(TelecomSite.objects.all().values(
                'site_name', 'site_code', 'area', 'region', 'province', 
                'city', 'address', 'latitude', 'longitude'
            ))
            
            # Convert Decimal to float for JSON serialization
            for site in sites:
                if 'latitude' in site and site['latitude'] is not None:
                    site['latitude'] = float(site['latitude'])
                if 'longitude' in site and site['longitude'] is not None:
                    site['longitude'] = float(site['longitude'])
            
            print(f"DEBUG: Loaded {len(sites)} sites from direct database query")
        except Exception as e:
            print(f"DEBUG: Direct database query failed: {e}")
    
    # Method 3: Fallback to JSON file
    if not sites:
        try:
            from .storage_methods import load_sites_from_json_file
            sites = load_sites_from_json_file()
            print(f"DEBUG: Loaded {len(sites)} sites from JSON file")
        except Exception as e:
            print(f"DEBUG: JSON file loading failed: {e}")
    
    # Method 4: Last resort - session
    if not sites:
        sites = session_sites
        print(f"DEBUG: Using session fallback with {len(sites)} sites")
    
    # Update session with whatever we found
    request.session['imported_sites'] = sites
    request.session.modified = True
    request.session.save()
    print(f"DEBUG: Updated session with {len(sites)} sites")
    
    # If still no sites, show message
    if not sites:
        print("DEBUG: WARNING - No sites found in any storage!")
    
    context = {
        'role': 'admin' if is_admin else 'user',
        'page_title': 'Telecom Sites Map',
        'sites': json.dumps(sites),  # Convert to JSON for JavaScript
        'is_admin': is_admin,
        'sites_count': len(sites)
    }
    
    return render(request, 'interventions/sites_map.html', context)

@csrf_exempt
@require_POST
@login_required
def clear_sites_cache(request):
    """
    Clear sites from database - ADMIN ONLY
    """
    # Use Django's built-in admin checks
    is_admin = request.user.is_superuser or request.user.is_staff
    
    print(f"DEBUG: Clear database attempt by {request.user.username}, is_admin: {is_admin}")
    
    if not is_admin:
        return JsonResponse({'error': 'Only administrators can clear sites data'}, status=403)
    
    try:
        # Clear all sites from database
        deleted_count = TelecomSite.objects.all().delete()[0]
        
        # Get remaining sites for response
        remaining_sites = list(TelecomSite.objects.all().values(
            'site_name', 'site_code', 'area', 'region', 'province', 
            'city', 'address', 'latitude', 'longitude'
        ))
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} sites from database. {len(remaining_sites)} sites remaining.',
            'sites': remaining_sites
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error clearing sites data: {str(e)}',
            'success': False
        }, status=500)

@csrf_exempt
@require_POST
@login_required
def import_sites_csv(request):
    """
    Handle CSV file upload and import sites data - ADMIN ONLY
    """
    # Use Django's built-in admin checks
    is_admin = request.user.is_superuser or request.user.is_staff
    
    if not is_admin:
        return JsonResponse({'error': 'Only administrators can upload CSV files'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        csv_file = request.FILES.get('sites_csv_file')
        if not csv_file:
            return JsonResponse({'error': 'No CSV file provided'}, status=400)
        
        # Check file extension
        if not csv_file.name.endswith('.csv'):
            return JsonResponse({'error': 'File must be a CSV file'}, status=400)
        
        # Read CSV file
        csv_file.seek(0)
        csv_data = csv_file.read().decode('utf-8').splitlines()
        
        sites = []
        
        # Handle Italian headers
        header_mapping = {
            'Codice SITO': 'site_name',
            'Cod internazionale': 'site_code', 
            'Area': 'area',
            'Regione': 'region',
            'Provincia': 'province',
            'Comune': 'city',
            'Indirizzo': 'address',
            'Latitude WGS84': 'latitude',
            'Longitude WGS84': 'longitude'
        }
        
        # Get headers from first row
        headers = []
        if csv_data:
            first_row = csv_data[0]
            # Handle both comma and semicolon delimiters
            if ';' in first_row:
                headers = [header.strip() for header in first_row.split(';')]
            else:
                headers = [header.strip() for header in first_row.split(',')]
        
        for row_num, row in enumerate(csv_data):
            if row_num == 0:  # Skip header row
                continue
                
            # Parse CSV row
            try:
                if ';' in row:
                    parts = [part.strip() for part in row.split(';')]
                else:
                    parts = [part.strip() for part in row.split(',')]
                
                # Map Italian headers to English field names
                site = {}
                for i, header in enumerate(headers):
                    if i < len(parts):
                        english_field = header_mapping.get(header, header.lower())
                        site[english_field] = parts[i]
                
                # Ensure required fields exist
                if not site.get('site_name'):
                    site['site_name'] = site.get('Codice SITO', '')
                if not site.get('address'):
                    site['address'] = site.get('Indirizzo', '')
                
                # Validate required fields
                if site.get('site_name') and site.get('address') and site.get('latitude') and site.get('longitude'):
                    sites.append(site)
                    
            except Exception as e:
                print(f"Error processing row {row_num}: {e}")
                continue
        
        # Save using hybrid storage (database + JSON file backup)
        if save_sites_hybrid(sites, request):
            # Load updated sites for response
            updated_sites = load_sites_hybrid()
            
            # Also save to session as additional backup
            request.session['imported_sites'] = updated_sites
            request.session.modified = True  # Ensure session is saved
            request.session.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully imported and saved {len(sites)} sites using hybrid storage (database + JSON file)',
                'sites': updated_sites
            })
        else:
            return JsonResponse({
                'error': 'Failed to save sites using hybrid storage',
                'success': False
            }, status=500)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error processing CSV: {str(e)}',
            'success': False
        }, status=500)
