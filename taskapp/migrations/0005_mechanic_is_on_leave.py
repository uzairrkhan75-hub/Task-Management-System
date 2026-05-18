from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskapp', '0004_alter_cars_options_task_promised_completion_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='mechanic',
            name='is_on_leave',
            field=models.BooleanField(
                default=False,
                help_text='Mark when the mechanic is unavailable (leave).',
            ),
        ),
    ]
