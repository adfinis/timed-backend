from django.db import migrations


def migrate_blocks(apps, schema_editor):
    Activity = apps.get_model('tracking', 'Activity')
    for activity in Activity.objects.all():
        if activity.blocks.count() == 1:
            block = activity.blocks.all()[0]
            activity.from_time = block.from_time
            activity.to_time = block.to_time
            activity.save()
        else:
            for block in activity.blocks.all():
                Activity(from_time=block.from_time,
                         to_time=block.to_time,
                         comment=activity.comment,
                         date=activity.date,
                         task=activity.task,
                         user=activity.user).save()


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0006_add_activity_time'),
    ]

    operations = [
        migrations.RunPython(migrate_blocks),
    ]
