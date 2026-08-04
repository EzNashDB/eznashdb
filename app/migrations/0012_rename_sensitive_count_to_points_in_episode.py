"""Renames AbuseState.sensitive_count_in_episode -> points_in_episode.

The field now holds accumulated per-request points (see app/rate_limiting.py),
not a flat count of "sensitive" requests, so the old name no longer matches
what it stores.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0011_reset_abuse_rate_limit_defaults"),
    ]

    operations = [
        migrations.RenameField(
            model_name="abusestate",
            old_name="sensitive_count_in_episode",
            new_name="points_in_episode",
        ),
    ]
