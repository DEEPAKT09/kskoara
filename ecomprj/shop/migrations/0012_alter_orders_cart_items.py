# Generated by Django 5.1.4 on 2024-12-27 04:50
import django
from django.db.models import JSONField 
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0011_orders_razorpay_order_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orders',
            name='cart_items',
            field=django.db.models.JSONField(default=list),
        ),
    ]
