# Generated manually to restore used_car field

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('interventions', '0001_initial'),
        ('fleet', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='intervention',
            name='used_car',
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='interventions',
                to='fleet.car'
            ),
        ),
    ]
