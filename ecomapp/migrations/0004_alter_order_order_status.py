# Generated by Django 4.0.2 on 2022-02-18 19:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecomapp', '0003_alter_order_order_status_admin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('Order Received', 'Order-Received'), ('Order Processing', 'Order-Processing'), ('on the way', 'on-the-way'), ('Order Completed', 'Order-Completed'), ('Order Cancelled', 'Order-Cancelled')], max_length=50),
        ),
    ]
