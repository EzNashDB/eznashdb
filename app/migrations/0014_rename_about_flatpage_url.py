from django.db import migrations

OLD_URL = "/about/"
NEW_URL = "/about-en/"


def rename_forward(apps, schema_editor):
    FlatPage = apps.get_model("flatpages", "FlatPage")
    FlatPage.objects.filter(url=OLD_URL).update(url=NEW_URL)


def rename_backward(apps, schema_editor):
    FlatPage = apps.get_model("flatpages", "FlatPage")
    FlatPage.objects.filter(url=NEW_URL).update(url=OLD_URL)


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0013_add_captcha_verified_at"),
        ("flatpages", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(rename_forward, rename_backward),
    ]
