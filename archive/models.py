
from django.db import models

class Project(models.Model):
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
    image = models.URLField(blank=True)
    description = models.TextField(blank=True)
    tools = models.CharField(max_length=300, blank=True)
    year = models.IntegerField(default=2026)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
