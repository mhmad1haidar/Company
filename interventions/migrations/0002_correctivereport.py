from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("interventions", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CorrectiveReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved"), ("rejected", "Rejected")], default="draft", max_length=20)),
                ("performed_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("fault_found", models.TextField(blank=True)),
                ("action_taken", models.TextField(blank=True)),
                ("work_summary", models.TextField(blank=True)),
                ("customer_notes", models.TextField(blank=True)),
                ("internal_notes", models.TextField(blank=True)),
                ("answers", models.JSONField(blank=True, default=dict)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approved_corrective_reports", to=settings.AUTH_USER_MODEL)),
                ("intervention", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="corrective_reports", to="interventions.intervention")),
                ("reporter", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="corrective_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="correctivereport",
            index=models.Index(fields=["intervention", "status"], name="interventio_interve_28519e_idx"),
        ),
        migrations.AddIndex(
            model_name="correctivereport",
            index=models.Index(fields=["reporter", "created_at"], name="interventio_reporte_47aa29_idx"),
        ),
    ]
