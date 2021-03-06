# Generated by Django 3.0.8 on 2020-11-20 15:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20201120_2136'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='brand',
            field=models.ForeignKey(default=9999, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Brand'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='item',
            name='color',
            field=models.ForeignKey(default=9999, on_delete=django.db.models.deletion.DO_NOTHING, to='core.Color'),
            preserve_default=False,
        ),
    ]
