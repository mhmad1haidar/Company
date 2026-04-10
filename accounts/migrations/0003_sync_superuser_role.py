from django.db import migrations


def sync_superuser_roles(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(is_superuser=True).update(role="admin")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_user_role_and_manager"),
    ]

    operations = [
        migrations.RunPython(sync_superuser_roles, migrations.RunPython.noop),
    ]
