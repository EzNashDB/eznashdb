# Generated by Django 4.0.1 on 2022-01-30 13:46

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('latitude', models.CharField(max_length=50)),
                ('longitude', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'city',
                'verbose_name_plural': 'cities',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('short_name', models.CharField(max_length=10)),
            ],
            options={
                'verbose_name': 'country',
                'verbose_name_plural': 'countries',
            },
        ),
        migrations.CreateModel(
            name='Shul',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('editted_by', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, default=list, null=True, size=None)),
                ('name', models.CharField(max_length=50)),
                ('has_female_leadership', models.BooleanField(blank=True, null=True)),
                ('has_childcare', models.BooleanField(blank=True, null=True)),
                ('has_kaddish_with_men', models.BooleanField(blank=True, null=True)),
                ('enum_has_kaddish_alone', models.CharField(blank=True, choices=[('YES', 'Yes'), ('NO', 'No'), ('MAN_ALWAYS_SAYS_KADDISH', 'Man always says kaddish')], max_length=50, null=True)),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shuls', to='eznashdb.city')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_shuls', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'shul',
                'verbose_name_plural': 'shuls',
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('relative_size', models.CharField(blank=True, choices=[('MUCH_SMALLER', 'Much smaller'), ('SOMEWHAT_SMALLER', 'Somewhat smaller'), ('SAME_SIZE', 'Same size'), ('LARGER', 'Larger')], max_length=50, null=True)),
                ('see_hear_score', models.IntegerField(blank=True, choices=[(1, ' 1 Very Difficult'), (2, ' 2 Difficult'), (3, ' 3 Average'), (4, ' 4 Easy'), (5, ' 5 Very Easy')], null=True)),
                ('is_centered', models.BooleanField(blank=True, default=False)),
                ('is_same_floor_side', models.BooleanField(blank=True, default=False)),
                ('is_same_floor_back', models.BooleanField(blank=True, default=False)),
                ('is_same_floor_elevated', models.BooleanField(blank=True, default=False)),
                ('is_same_floor_level', models.BooleanField(blank=True, default=False)),
                ('is_balcony_side', models.BooleanField(blank=True, default=False)),
                ('is_balcony_back', models.BooleanField(blank=True, default=False)),
                ('is_only_men', models.BooleanField(blank=True, default=False)),
                ('is_mixed_seating', models.BooleanField(blank=True, default=False)),
                ('is_wheelchair_accessible', models.BooleanField(blank=True, default=False)),
                ('shul', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='rooms', to='eznashdb.shul')),
            ],
            options={
                'verbose_name': 'room',
                'verbose_name_plural': 'rooms',
            },
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('is_default_region', models.BooleanField(blank=True, default=False, null=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='regions', to='eznashdb.country')),
            ],
            options={
                'verbose_name': 'region',
                'verbose_name_plural': 'regions',
            },
        ),
        migrations.AddField(
            model_name='city',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cities', to='eznashdb.region'),
        ),
    ]