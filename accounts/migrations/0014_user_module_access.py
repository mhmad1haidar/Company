from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_quickaction_userquickaction"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="module_access",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
