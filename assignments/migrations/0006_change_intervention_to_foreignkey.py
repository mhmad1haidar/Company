# Generated to allow multiple assignments per intervention

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0005_workassignment_work_performed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workassignment',
            name='intervention',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='work_assignments',
                to='interventions.intervention',
                verbose_name='Intervention'
            ),
        ),
    ]
