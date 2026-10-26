from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('archive', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='project', name='project_date',
            field=models.DateField(blank=True, null=True, help_text='Optional exact project date. The year is used when this is empty.'),
        ),
        migrations.AddField(
            model_name='project', name='dominant_color',
            field=models.CharField(blank=True, max_length=20,
                choices=[('red', 'Red'), ('orange', 'Orange'), ('yellow', 'Yellow'),
                         ('green', 'Green'), ('blue', 'Blue'), ('purple', 'Purple'),
                         ('pink', 'Pink'), ('brown', 'Brown'), ('black', 'Black'),
                         ('white', 'White'), ('gray', 'Gray'), ('multicolor', 'Multicolor')],
                help_text='Main color of the artwork, used by Atlas filters.'),
        ),
    ]
