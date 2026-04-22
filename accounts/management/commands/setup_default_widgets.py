from django.core.management.base import BaseCommand
from accounts.models import Widget, UserWidget, User


class Command(BaseCommand):
    help = 'Set up default widgets for different user roles'

    def handle(self, *args, **options):
        # Create default widgets
        widgets_data = [
            {
                'name': 'Attendance Stats',
                'widget_type': Widget.WidgetType.ATTENDANCE,
                'description': 'Show attendance statistics for the current month',
                'icon': 'bi-clock',
                'order': 1,
            },
            {
                'name': 'Recent Assignments',
                'widget_type': Widget.WidgetType.ASSIGNMENTS,
                'description': 'Display recent task assignments',
                'icon': 'bi-clipboard-check',
                'order': 2,
            },
            {
                'name': 'Announcements',
                'widget_type': Widget.WidgetType.ANNOUNCEMENTS,
                'description': 'Show latest announcements',
                'icon': 'bi-megaphone',
                'order': 3,
            },
            {
                'name': 'Unread Messages',
                'widget_type': Widget.WidgetType.MESSAGES,
                'description': 'Display unread message count',
                'icon': 'bi-envelope',
                'order': 4,
            },
            {
                'name': 'Leave Balance',
                'widget_type': Widget.WidgetType.LEAVE,
                'description': 'Show leave balance information',
                'icon': 'bi-calendar3',
                'order': 5,
            },
            {
                'name': 'Notifications',
                'widget_type': Widget.WidgetType.NOTIFICATIONS,
                'description': 'Display recent notifications',
                'icon': 'bi-bell',
                'order': 6,
            },
            {
                'name': 'Quick Actions',
                'widget_type': Widget.WidgetType.QUICK_ACTIONS,
                'description': 'Quick access to common actions',
                'icon': 'bi-lightning',
                'order': 7,
            },
            {
                'name': 'Calendar',
                'widget_type': Widget.WidgetType.CALENDAR,
                'description': 'Show calendar view',
                'icon': 'bi-calendar',
                'order': 8,
            },
        ]

        created_widgets = []
        for widget_data in widgets_data:
            widget, created = Widget.objects.get_or_create(
                name=widget_data['name'],
                defaults=widget_data
            )
            if created:
                created_widgets.append(widget)
                self.stdout.write(f'Created widget: {widget.name}')
            else:
                self.stdout.write(f'Widget already exists: {widget.name}')

        # Configure widgets for different user roles
        admin_widgets = widgets_data  # All widgets for admin
        manager_widgets = [
            w for w in widgets_data if w['widget_type'] in [
                Widget.WidgetType.ATTENDANCE,
                Widget.WidgetType.ASSIGNMENTS,
                Widget.WidgetType.ANNOUNCEMENTS,
                Widget.WidgetType.MESSAGES,
                Widget.WidgetType.LEAVE,
                Widget.WidgetType.NOTIFICATIONS,
                Widget.WidgetType.QUICK_ACTIONS,
            ]
        ]
        employee_widgets = [
            w for w in widgets_data if w['widget_type'] in [
                Widget.WidgetType.ATTENDANCE,
                Widget.WidgetType.ASSIGNMENTS,
                Widget.WidgetType.ANNOUNCEMENTS,
                Widget.WidgetType.MESSAGES,
                Widget.WidgetType.LEAVE,
                Widget.WidgetType.NOTIFICATIONS,
                Widget.WidgetType.QUICK_ACTIONS,
            ]
        ]

        # Assign widgets to users based on role
        for user in User.objects.filter(is_active=True):
            if user.role == User.Role.ADMIN:
                role_widgets = admin_widgets
            elif user.role == User.Role.MANAGER:
                role_widgets = manager_widgets
            else:
                role_widgets = employee_widgets

            for i, widget_data in enumerate(role_widgets):
                widget = Widget.objects.get(name=widget_data['name'])
                UserWidget.objects.get_or_create(
                    user=user,
                    widget=widget,
                    defaults={'is_enabled': True, 'order': i + 1}
                )

            self.stdout.write(f'Configured widgets for user: {user.username} (role: {user.role})')

        self.stdout.write(self.style.SUCCESS('Successfully set up default widgets for all users'))
