from django.contrib import admin
from .models import Project, CurationSubmission
from django.db import transaction
from django.contrib import messages
from django.utils.html import format_html
from . import discovery


class DiscoveryFilter(admin.SimpleListFilter):
    def lookups(self, request, model_admin):
        return self.choices_list

    def queryset(self, request, queryset):
        if self.value() in dict(self.choices_list):
            return queryset.filter(pk__in=[project.pk for project in queryset
                                          if self.resolve(project) == self.value()])
        return queryset


class ProjectTypeFilter(DiscoveryFilter):
    title, parameter_name = 'type', 'discovery_type'
    choices_list = Project.PROJECT_TYPE_CHOICES
    resolve = staticmethod(discovery.project_type)


class MediaFormatFilter(DiscoveryFilter):
    title, parameter_name = 'format', 'discovery_format'
    choices_list = Project.FORMAT_CHOICES
    resolve = staticmethod(discovery.media_format)


class CreativeFieldFilter(DiscoveryFilter):
    title, parameter_name = 'creative field', 'discovery_field'
    choices_list = Project.CREATIVE_FIELD_CHOICES
    resolve = staticmethod(discovery.creative_field)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'discovery_type', 'discovery_format', 'discovery_field', 'year', 'dominant_color')
    search_fields = ('title', 'artist', 'description', 'instagram_username', 'tools')
    list_filter = (ProjectTypeFilter, MediaFormatFilter, CreativeFieldFilter, 'category', 'year', 'dominant_color', 'country')
    readonly_fields = ('automatic_classification', 'gallery_preview')

    @admin.display(description='Classification used by Atlas filters and maps')
    def automatic_classification(self, obj):
        if not obj or not obj.pk:
            return 'Save the project to see its automatic labels. Leave Type, Format and Creative field blank for automatic classification.'
        from .classification import describe
        choices = {'project_type': dict(Project.PROJECT_TYPE_CHOICES), 'media_format': dict(Project.FORMAT_CHOICES),
                   'creative_field': dict(Project.CREATIVE_FIELD_CHOICES)}
        return ' · '.join(f'{field.replace("_", " ").title()}: {choices[field][item["value"]]} ({item["source"]})'
                          for field, item in describe(obj).items())

    @admin.display(description='Optimized gallery cover')
    def gallery_preview(self, obj):
        if obj and obj.thumbnail_file and obj.thumbnail_source == obj.cover_file.name:
            return '320px WebP ready. The full cover is preserved for the project page.'
        return 'Upload a cover file to generate a lightweight gallery image automatically. Remote image URLs use the original image.'

    @admin.display(description='Type')
    def discovery_type(self, obj):
        return dict(Project.PROJECT_TYPE_CHOICES)[discovery.project_type(obj)]

    @admin.display(description='Format')
    def discovery_format(self, obj):
        return dict(Project.FORMAT_CHOICES)[discovery.media_format(obj)]

    @admin.display(description='Creative field')
    def discovery_field(self, obj):
        return dict(Project.CREATIVE_FIELD_CHOICES)[discovery.creative_field(obj)]


@admin.register(CurationSubmission)
class CurationSubmissionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'publisher', 'media_type', 'published_on', 'status', 'ai_confirmed', 'original_link')
    list_filter = ('status', 'media_type', 'ai_confirmed', 'publisher')
    search_fields = ('title', 'suggested_title', 'publisher', 'artist', 'source_key', 'source_url')
    readonly_fields = ('source_key', 'suggested_title', 'caption_excerpt', 'preview_url', 'project', 'created_at', 'original_link')
    actions = ['publish_reviewed']
    fieldsets = (
        ('Source evidence', {'fields': ('source_key', 'source_url', 'original_link', 'publisher',
                                       'media_type', 'published_on', 'caption_excerpt', 'suggested_title', 'preview_url')}),
        ('Review and complete before publishing', {'fields': ('title', 'artist', 'category', 'project_year',
                                                             'tools', 'image_url', 'description', 'ai_confirmed', 'notes')}),
        ('Tracking', {'fields': ('status', 'project', 'created_at')}),
    )

    @admin.display(description='Original post')
    def original_link(self, obj):
        return format_html('<a href="{}" target="_blank" rel="noopener noreferrer">Open Instagram ↗</a>', obj.source_url)

    @admin.action(description='Publish reviewed submissions to the Atlas', permissions=['change'])
    def publish_reviewed(self, request, queryset):
        if not request.user.has_perm('archive.add_project'):
            self.message_user(request, 'You need permission to add projects.', messages.ERROR)
            return
        published = skipped = 0
        with transaction.atomic():
            for submission in queryset.select_for_update():
                if (submission.project_id or submission.status != 'pending' or not submission.ai_confirmed
                        or not submission.title.strip() or not submission.artist.strip()
                        or not submission.category or not submission.project_year):
                    skipped += 1
                    continue
                submission.project = Project.objects.create(
                    title=submission.title, artist=submission.artist, category=submission.category,
                    year=submission.project_year, tools=submission.tools, image=submission.image_url,
                    description=submission.description, source_url=submission.source_url,
                )
                submission.status = 'published'
                submission.save(update_fields=['project', 'status'])
                published += 1
        self.message_user(request, f'{published} published; {skipped} skipped (incomplete, rejected or already published).')
