from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("tracking", "0007_migrate_activity_blocks")]

    operations = [
        migrations.RemoveField(model_name="activityblock", name="activity"),
        migrations.DeleteModel(name="ActivityBlock"),
    ]
