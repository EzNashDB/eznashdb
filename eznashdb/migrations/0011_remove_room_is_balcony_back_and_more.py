# Generated by Django 4.0.1 on 2023-05-21 08:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eznashdb', '0010_room_is_balcony'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='room',
            name='is_balcony_back',
        ),
        migrations.RemoveField(
            model_name='room',
            name='is_balcony_side',
        ),
    ]
