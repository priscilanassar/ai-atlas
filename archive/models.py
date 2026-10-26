
from django.db import models

class Project(models.Model):
    PROJECT_TYPE_CHOICES = [('art', 'Art'), ('brand', 'Brand Project'), ('experiment', 'Experiment')]
    FORMAT_CHOICES = [('image', 'Image'), ('video', 'Video'), ('series', 'Series')]
    CREATIVE_FIELD_CHOICES = [
        ('art', 'Visual Art'), ('fashion', 'Fashion'), ('film', 'Film'),
        ('design', 'Design'), ('architecture', 'Architecture'),
        ('abstract', 'Abstract Art'), ('3d', 'CGI / 3D'),
    ]
    COLOR_CHOICES = [
        ('red', 'Red'), ('orange', 'Orange'), ('yellow', 'Yellow'),
        ('green', 'Green'), ('blue', 'Blue'), ('purple', 'Purple'),
        ('pink', 'Pink'), ('brown', 'Brown'), ('black', 'Black'),
        ('white', 'White'), ('gray', 'Gray'), ('multicolor', 'Multicolor'),
    ]
    CATEGORY_CHOICES = [
        ('AI', 'AI Art'),
        ('CGI', 'CGI / 3D'),
        ('FASHION', 'Digital Fashion'),
        ('FILM', 'AI Film'),
        ('DESIGN', 'Graphic Design'),
    ]

    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    image = models.URLField(blank=True, max_length=4000)
    description = models.TextField(blank=True)
    tools = models.CharField(max_length=300, blank=True, help_text='Tools disclosed for this work, separated by commas or semicolons.')
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, blank=True,
                                   help_text='Optional curator override. Leave blank to use the project description.')
    media_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, blank=True,
                                   help_text='Optional curator override. Leave blank to use the source and project media.')
    creative_field = models.CharField(max_length=20, choices=CREATIVE_FIELD_CHOICES, blank=True,
                                     help_text='Optional curator override. Leave blank to use the project category.')
    year = models.IntegerField(default=2026)
    project_date = models.DateField(blank=True, null=True, help_text='Optional exact project date. The year is used when this is empty.')
    dominant_color = models.CharField(max_length=20, choices=COLOR_CHOICES, blank=True,
                                      help_text='Main color of the artwork, used by Atlas filters.')
    created_at = models.DateTimeField(auto_now_add=True)
    country = models.CharField(max_length=100, blank=True, help_text='Confirmed country where this work was made, in English. Leave blank when not documented; do not infer nationality.')
    country_evidence = models.CharField(max_length=500, blank=True, help_text='Source URL or direct confirmation for the production country.')
    city = models.CharField(max_length=100, blank=True, help_text='City of the artist or studio.')
    source_url = models.URLField(blank=True, max_length=1000, help_text='Original project or publication.')
    instagram_shortcode = models.CharField(max_length=30, null=True, blank=True, unique=True)
    instagram_username = models.CharField(max_length=100, blank=True)
    instagram_caption = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    cover_file = models.FileField(upload_to='projects/covers/', blank=True)
    thumbnail_file = models.FileField(upload_to='projects/thumbnails/', blank=True, editable=False)
    thumbnail_source = models.CharField(max_length=500, blank=True, editable=False)
    media_items = models.JSONField(default=list, blank=True)
    title_is_editorial = models.BooleanField(default=False)
    ai_disclosure = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.dominant_color and self.cover_file:
            from .colors import detect_color
            try:
                if self.cover_file._committed:
                    with self.cover_file.open('rb') as cover:
                        self.dominant_color = detect_color(cover)
                else:
                    self.dominant_color = detect_color(self.cover_file.file)
                    self.cover_file.seek(0)
                if kwargs.get('update_fields') is not None:
                    kwargs['update_fields'] = set(kwargs['update_fields']) | {'dominant_color'}
            except (OSError, ValueError):
                pass  # Missing or unsupported covers can still be curated manually.
        super().save(*args, **kwargs)
        if kwargs.get('update_fields') is None or 'cover_file' in kwargs['update_fields']:
            from .thumbnails import prepare_thumbnail
            try:
                if prepare_thumbnail(self):
                    type(self).objects.using(self._state.db).filter(pk=self.pk).update(
                        thumbnail_file=self.thumbnail_file.name, thumbnail_source=self.thumbnail_source)
            except (OSError, ValueError):
                import logging
                logging.getLogger(__name__).warning('Thumbnail unavailable for project %s; keeping original cover.', self.pk)

    @property
    def creator_credit(self):
        from .discovery import creator_names
        return ' / '.join(creator_names(self))

    @property
    def cover_url(self):
        return self.cover_file.url if self.cover_file else self.image

    @property
    def thumbnail_url(self):
        if self.thumbnail_file and self.cover_file and self.thumbnail_source == self.cover_file.name:
            return self.thumbnail_file.url
        return self.cover_url

    @property
    def preview_video_url(self):
        return next((item.get('preview_url', '') for item in self.media_items
                     if item.get('kind') == 'video' and item.get('preview_url')), '')

    @property
    def primary_video(self):
        return next((item for item in self.media_items if item.get('kind') == 'video'), None)

    @property
    def instagram_profile_url(self):
        return f'https://www.instagram.com/{self.instagram_username}/' if self.instagram_username else ''

    def __str__(self):
        return self.title


class CurationSubmission(models.Model):
    source_key = models.CharField(max_length=100, unique=True)
    source_url = models.URLField(max_length=1000)
    media_type = models.CharField(max_length=10, choices=[('post', 'Post'), ('reel', 'Reel')])
    publisher = models.CharField(max_length=100, blank=True, help_text='Publishing account; not necessarily the original artist.')
    published_on = models.DateField(null=True, blank=True, help_text='Instagram publication date, not project creation date.')
    caption_excerpt = models.TextField(blank=True)
    suggested_title = models.CharField(max_length=200, blank=True, help_text='First line of the caption; may not be the work title.')
    preview_url = models.URLField(max_length=4000, blank=True, help_text='Temporary Instagram preview URL; may expire or show the first carousel slide.')
    title = models.CharField(max_length=200, blank=True)
    artist = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=20, choices=Project.CATEGORY_CHOICES, blank=True)
    project_year = models.IntegerField(null=True, blank=True)
    tools = models.CharField(max_length=300, blank=True)
    image_url = models.URLField(blank=True, help_text='Reviewed cover image URL to use in the Atlas.')
    description = models.TextField(blank=True)
    ai_confirmed = models.BooleanField(default=False, help_text='Confirm the project uses AI before adding it to the Atlas.')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending review'), ('published', 'Published'), ('rejected', 'Rejected')])
    project = models.OneToOneField(Project, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name='curation_submission')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'curation submission'
        verbose_name_plural = 'curation inbox'
        ordering = ['-created_at']

    def __str__(self):
        return self.title or f'@{self.publisher or "unknown"} · {self.source_key.split(":")[-1]}'
