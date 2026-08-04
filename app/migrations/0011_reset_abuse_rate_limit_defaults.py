from django.db import migrations

STALE_KEYS = ["ABUSE_RATE_LIMIT", "ABUSE_SENSITIVE_CAP_PER_EPISODE"]


def reset_stale_defaults(apps, schema_editor):
    Constance = apps.get_model("constance", "Constance")
    Constance.objects.filter(key__in=STALE_KEYS).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0010_rename_points_to_strikes"),
        ("constance", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(reset_stale_defaults, noop),
    ]
