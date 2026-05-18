from django.db import migrations


def rename_shop_manager_to_manager(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Shop Manager').update(name='Manager')
    Group.objects.get_or_create(name='Manager')


def noop_reverse(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Manager').update(name='Shop Manager')


class Migration(migrations.Migration):

    dependencies = [
        ('taskapp', '0008_mechanic_user'),
    ]

    operations = [
        migrations.RunPython(rename_shop_manager_to_manager, noop_reverse),
    ]
