from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('archive', '0002_project_date_dominant_color')]
    operations = [
        migrations.AddField(model_name='project', name='country', field=models.CharField(
            max_length=100, blank=True, help_text='Country of the artist or studio.')),
        migrations.AddField(model_name='project', name='city', field=models.CharField(
            max_length=100, blank=True, help_text='City of the artist or studio.')),
    ]
