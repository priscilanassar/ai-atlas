
from django import forms
from .models import Collection


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection

        fields = [
            'title',
            'description',
            'cover_image',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Collection name',
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe your collection...',
                'rows': 4,
            }),
            'cover_image': forms.URLInput(attrs={
                'placeholder': 'https://image-url.com',
            }),
        }
