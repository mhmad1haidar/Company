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

# Create a mock request
factory = RequestFactory()
request = factory.get('/attendance/timesheet/?month=10&year=2024&format=excel&employee=all')

# Mock user
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.first()
request.user = user

# Test the view
view = TimesheetDownloadView()
try:
    response = view.get(request)
    print(f"Response type: {type(response)}")
    print(f"Status code: {response.status_code}")
    print(f"Content type: {response.get('Content-Type', 'Not set')}")
    print(f"Content length: {len(response.content) if hasattr(response, 'content') else 'N/A'}")
    
    # Save test file
    if hasattr(response, 'content'):
        with open('direct_test.xlsx', 'wb') as f:
            f.write(response.content)
        print("Test file saved as 'direct_test.xlsx'")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
