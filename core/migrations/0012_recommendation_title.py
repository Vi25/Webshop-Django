# Generated by Django 2.2.14 on 2020-12-06 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20201206_2037'),
    ]

    operations = [
        migrations.AddField(
            model_name='recommendation',
            name='title',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
