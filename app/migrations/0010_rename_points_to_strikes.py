"""Renames AbuseState.points -> strikes (see AbuseState.points for why).

Also deletes the Constance row for ABUSE_POINTS_DECAY_HOURS, renamed to
ABUSE_STRIKES_DECAY_HOURS here: Constance caches a value in the DB on first
read and never cleans up a key that's been renamed out of CONSTANCE_CONFIG,
so the old row would otherwise linger forever.
"""

from django.db import migrations


def delete_orphaned_constance_key(apps, schema_editor):
    Constance = apps.get_model("constance", "Constance")
    Constance.objects.filter(key="ABUSE_POINTS_DECAY_HOURS").delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0009_google_places_usage"),
        ("constance", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="abusestate",
            old_name="points",
            new_name="strikes",
        ),
        migrations.RenameField(
            model_name="abusestate",
            old_name="last_points_update_at",
            new_name="last_strikes_update_at",
        ),
        migrations.RunPython(delete_orphaned_constance_key, noop),
    ]
