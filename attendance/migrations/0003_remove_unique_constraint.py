# Generated to allow multiple check-ins/check-outs per day

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_professional_models'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='attendance',
            name='uniq_attendance_user_date',
        ),
    ]
