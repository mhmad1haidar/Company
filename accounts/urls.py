from django.urls import path

from . import views
from . import profile_views
from . import views_employee

app_name = "accounts"

urlpatterns = [
    path("login/", views.AppLoginView.as_view(), name="login"),
    path("logout/", views.AppLogoutView.as_view(), name="logout"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("profile/", profile_views.UserProfileView.as_view(), name="profile"),
    path("settings/", profile_views.UserSettingsView.as_view(), name="settings"),
    
    # Notifications
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path("notifications/<int:pk>/", views.NotificationDetailView.as_view(), name="notification-detail"),
    path("notifications/mark-read/", views.MarkAllAsReadView.as_view(), name="mark-all-read"),
    path("notifications/count/", views.NotificationCountView.as_view(), name="notification-count"),
    path("notifications/recent/", views.RecentNotificationsView.as_view(), name="recent-notifications"),
    
    # Dark mode toggle
    path("toggle-dark-mode/", views.toggle_dark_mode, name="toggle-dark-mode"),

    # Announcements
    path("announcements/", views.AnnouncementListView.as_view(), name="announcement-list"),
    path("announcements/<int:pk>/", views.AnnouncementDetailView.as_view(), name="announcement-detail"),
    path("announcements/create/", views.AnnouncementCreateView.as_view(), name="announcement-create"),
    path("announcements/<int:pk>/edit/", views.AnnouncementUpdateView.as_view(), name="announcement-update"),
    path("announcements/<int:pk>/delete/", views.AnnouncementDeleteView.as_view(), name="announcement-delete"),
    path("announcements/dashboard/", views.AnnouncementDashboardView.as_view(), name="announcement-dashboard"),

    # Messages
    path("messages/inbox/", views.MessageInboxView.as_view(), name="message-inbox"),
    path("messages/sent/", views.MessageSentView.as_view(), name="message-sent"),
    path("messages/<int:pk>/", views.MessageDetailView.as_view(), name="message-detail"),
    path("messages/compose/", views.MessageComposeView.as_view(), name="message-compose"),
    path("messages/<int:pk>/reply/", views.MessageReplyView.as_view(), name="message-reply"),
    
    # Employee management
    path("employees/", views_employee.employee_list, name="employee-list"),
    path("employees/archive/", views_employee.employee_archive, name="employee-archive"),
    path("employees/create/", views_employee.employee_create, name="employee-create"),
    path("employees/<int:pk>/", views_employee.employee_detail, name="employee-detail"),
    path("employees/<int:pk>/edit/", views_employee.employee_edit, name="employee-edit"),
    path("employees/<int:pk>/profile/", views_employee.employee_profile_edit, name="employee-profile-edit"),
    path("employees/<int:pk>/documents/", views_employee.employee_documents, name="employee-documents"),
    path("employees/<int:employee_pk>/documents/<int:doc_pk>/verify/", views_employee.document_verify, name="employee-document-verify"),
    path("employees/<int:employee_pk>/documents/<int:doc_pk>/delete/", views_employee.document_delete, name="employee-document-delete"),
    path("employees/<int:pk>/skills/", views_employee.employee_skills, name="employee-skills"),
    path("employees/<int:employee_pk>/skills/<int:skill_pk>/delete/", views_employee.skill_delete, name="employee-skill-delete"),
    path("employees/<int:pk>/assets/", views_employee.employee_assets, name="employee-assets"),
    path("employees/<int:employee_pk>/assets/<int:asset_pk>/return/", views_employee.asset_return, name="employee-asset-return"),
    path("employees/<int:employee_pk>/assets/<int:asset_pk>/delete/", views_employee.asset_delete, name="employee-asset-delete"),
    
    # Department management
    path("departments/", views_employee.department_list, name="department-list"),
    path("departments/create/", views_employee.department_create, name="department-create"),
    path("departments/<int:pk>/edit/", views_employee.department_edit, name="department-edit"),
]
