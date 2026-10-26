from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('archive', '0007_project_country_evidence_alter_project_country')]
    operations = [
        migrations.AddField(model_name='project', name='thumbnail_file', field=models.FileField(upload_to='projects/thumbnails/', blank=True, editable=False)),
        migrations.AddField(model_name='project', name='thumbnail_source', field=models.CharField(max_length=500, blank=True, editable=False)),
    ]
