# Generated by Django 2.2.16 on 2022-02-03 15:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_comment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['created']},
        ),
    ]
