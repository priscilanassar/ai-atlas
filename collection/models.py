
from django.db import models
from django.contrib.auth.models import User
from archive.models import Project


class Collection(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cover_image = models.URLField(blank=True)

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='creative_collections'
    )

    projects = models.ManyToManyField(
        Project,
        blank=True,
        related_name='collection'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
