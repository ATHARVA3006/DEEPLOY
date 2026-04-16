from django import forms
from django.contrib.auth.models import User
from .models import Folder, UserLink, UserProfile


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name', 'description', 'is_public', 'tags']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'My Project Files'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Optional description'}),
            'tags': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'html, css, javascript (comma separated)'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
        }


class UserLinkForm(forms.ModelForm):
    class Meta:
        model = UserLink
        fields = ['title', 'url', 'icon']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'GitHub Profile'}),
            'url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://github.com/username'}),
            'icon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '🔗 (emoji or text)'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'phone', 'gender', 'date_of_birth', 'website', 'location', 'company', 'github', 'twitter', 'linkedin']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Tell us about yourself'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+1 234 567 8900'}),
            'gender': forms.Select(attrs={'class': 'form-input'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'website': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://yoursite.com'}),
            'location': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City, Country'}),
            'company': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your Company'}),
            'github': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://github.com/username'}),
            'twitter': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://twitter.com/username'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://linkedin.com/in/username'}),
        }
