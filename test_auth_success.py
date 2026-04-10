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

# Create a mock request with authenticated user
factory = RequestFactory()
request = factory.get('/attendance/timesheet/?month=10&year=2024&format=excel&employee=all')

# Mock authenticated user
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.first()

# Create a mock user with is_authenticated property
class MockUser:
    def __init__(self, real_user):
        self.real_user = real_user
        self.is_authenticated = True
        self.is_staff = real_user.is_staff
        self.role = getattr(real_user, 'role', 'employee')
    
    def __getattr__(self, name):
        return getattr(self.real_user, name)

request.user = MockUser(user)

# Test the view
view = TimesheetDownloadView()
try:
    response = view.dispatch(request)
    print(f"Response type: {type(response)}")
    print(f"Status code: {response.status_code}")
    print(f"Content type: {response.get('Content-Type', 'Not set')}")
    if hasattr(response, 'url'):
        print(f"Redirect URL: {response.url}")
    else:
        print("No redirect - file download should work!")
        if hasattr(response, 'content'):
            print(f"Content length: {len(response.content)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
