# Generated by Django 3.0.8 on 2020-11-21 03:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20201120_2253'),
    ]

    operations = [
        migrations.RenameField(
            model_name='item',
            old_name='image_large_url',
            new_name='large_image_url',
        ),
        migrations.RenameField(
            model_name='item',
            old_name='image_medium_url',
            new_name='medium_image_url',
        ),
        migrations.RenameField(
            model_name='item',
            old_name='image_small_url',
            new_name='small_image_url',
        ),
        migrations.AddField(
            model_name='item',
            name='asin',
            field=models.CharField(max_length=15, null=True),
        ),
    ]
