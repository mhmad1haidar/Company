from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0014_user_module_access"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(
                choices=[
                    ("leave_request", "Leave Request"),
                    ("leave_approved", "Leave Approved"),
                    ("leave_rejected", "Leave Rejected"),
                    ("attendance_late", "Late Check-in"),
                    ("attendance_absent", "Absent"),
                    ("attendance_missing_checkout", "Missing Check-out"),
                    ("assignment_new", "New Assignment"),
                    ("assignment_status_change", "Assignment Status Change"),
                    ("assignment_deadline", "Assignment Deadline"),
                    ("intervention_new", "New Intervention"),
                    ("intervention_status_change", "Intervention Status Change"),
                    ("message_new", "New Message"),
                    ("message_reply", "Message Reply"),
                    ("announcement_new", "New Announcement"),
                    ("system", "System"),
                ],
                max_length=50,
            ),
        ),
    ]
