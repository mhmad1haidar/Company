# Generated manually to restore vehicle field

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0011_alter_workassignment_status'),
        ('fleet', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workassignment',
            name='vehicle',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='work_assignments',
                to='fleet.car',
                verbose_name='Vehicle'
            ),
        ),
    ]
