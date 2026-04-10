from django.db import migrations


def seed_leave_types(apps, schema_editor):
    LeaveType = apps.get_model("leave", "LeaveType")
    seeds = [
        ("sick", "Sick leave", ""),
        ("vacation", "Vacation", ""),
        ("personal", "Personal day", ""),
        ("unpaid", "Unpaid leave", ""),
        ("other", "Other", ""),
    ]
    for code, name, description in seeds:
        LeaveType.objects.get_or_create(
            code=code,
            defaults={"name": name, "description": description},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("leave", "0002_professional_models"),
    ]

    operations = [
        migrations.RunPython(seed_leave_types, migrations.RunPython.noop),
    ]
