#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'company.settings.development')
django.setup()

from django.http import HttpResponse
from django.test import RequestFactory
from attendance.views import TimesheetDownloadView

# Create a mock request without user
factory = RequestFactory()
request = factory.get('/attendance/timesheet/?month=10&year=2024&format=excel&employee=all')

# No user set (simulating unauthenticated request)
request.user = None

# Test the view
view = TimesheetDownloadView()
try:
    response = view.dispatch(request)
    print(f"Response type: {type(response)}")
    print(f"Status code: {response.status_code}")
    print(f"Content type: {response.get('Content-Type', 'Not set')}")
    if hasattr(response, 'url'):
        print(f"Redirect URL: {response.url}")
    print(f"Response content preview: {response.content[:200] if hasattr(response, 'content') else 'No content'}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
