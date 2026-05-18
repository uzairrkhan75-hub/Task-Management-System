from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskapp', '0005_mechanic_is_on_leave'),
    ]

    operations = [
        migrations.AddField(
            model_name='mechanic',
            name='is_manually_busy',
            field=models.BooleanField(
                default=False,
                help_text='When set and there is no open task, shows as Busy.',
            ),
        ),
    ]
