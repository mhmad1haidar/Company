from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta, date
import json

from attendance.models import Attendance
from django.contrib.auth import get_user_model


class AttendanceAnalyticsView(LoginRequiredMixin, View):
    """API endpoint for attendance analytics data."""
    
    def get(self, request, *args, **kwargs):
        # Get date range for the last 30 days
        today = timezone.now().date()
        start_date = today - timedelta(days=29)  # Last 30 days including today
        
        # Get attendance data for the last 30 days
        attendance_data = Attendance.objects.filter(
            date__gte=start_date,
            date__lte=today
        ).order_by('date')
        
        # Aggregate data per day
        daily_data = {}
        all_users = get_user_model().objects.filter(is_active=True)
        total_users = all_users.count()
        
        # Initialize all dates with zero counts
        current_date = start_date
        while current_date <= today:
            daily_data[current_date.isoformat()] = {
                'date': current_date.isoformat(),
                'present': 0,
                'absent': 0,
                'total': total_users
            }
            current_date += timedelta(days=1)
        
        # Fill in actual attendance data
        for attendance in attendance_data:
            date_str = attendance.date.isoformat()
            if date_str in daily_data:
                if attendance.check_in:
                    daily_data[date_str]['present'] += 1
                # Note: We don't count absent here - it's calculated below
        
        # Calculate absent count for each day
        for date_str in daily_data:
            present = daily_data[date_str]['present']
            daily_data[date_str]['absent'] = total_users - present
        
        # Prepare data for line chart (attendance per day)
        line_chart_data = {
            'labels': [],
            'datasets': [{
                'label': 'Present',
                'data': [],
                'borderColor': '#10b981',
                'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                'tension': 0.4,
                'fill': True
            }, {
                'label': 'Absent',
                'data': [],
                'borderColor': '#ef4444',
                'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                'tension': 0.4,
                'fill': True
            }]
        }
        
        # Fill line chart data
        for date_str in sorted(daily_data.keys()):
            daily_data[date_str] = daily_data[date_str]
            line_chart_data['labels'].append(date_str)
            line_chart_data['datasets'][0]['data'].append(daily_data[date_str]['present'])
            line_chart_data['datasets'][1]['data'].append(daily_data[date_str]['absent'])
        
        # Calculate overall present vs absent for pie chart
        total_present = sum(data['present'] for data in daily_data.values())
        total_absent = sum(data['absent'] for data in daily_data.values())
        
        pie_chart_data = {
            'labels': ['Present', 'Absent'],
            'datasets': [{
                'data': [total_present, total_absent],
                'backgroundColor': ['#10b981', '#ef4444'],
                'borderWidth': 2,
                'borderColor': '#ffffff'
            }]
        }
        
        # Summary statistics
        summary = {
            'total_days': len(daily_data),
            'total_present': total_present,
            'total_absent': total_absent,
            'attendance_rate': round((total_present / (total_present + total_absent)) * 100, 1) if (total_present + total_absent) > 0 else 0,
            'total_employees': total_users
        }
        
        return JsonResponse({
            'line_chart': line_chart_data,
            'pie_chart': pie_chart_data,
            'summary': summary,
            'daily_data': list(daily_data.values())
        })
