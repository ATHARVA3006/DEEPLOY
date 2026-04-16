from django.contrib import admin
from .models import Folder, File, UserLink, Subscription, UserProfile, ActivityLog, Notification


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'is_public', 'visits', 'created_at']
    list_filter = ['is_public', 'is_featured']
    search_fields = ['name', 'owner__username']


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['name', 'folder', 'file_type', 'size', 'downloads', 'uploaded_at']
    search_fields = ['name', 'folder__name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'is_verified', 'is_banned']
    list_filter = ['is_verified', 'is_banned']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'is_active', 'started_at']
    list_filter = ['plan', 'is_active']


@admin.register(UserLink)
class UserLinkAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'url', 'order']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'created_at']
    list_filter = ['action']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'type', 'is_read', 'created_at']
    list_filter = ['type', 'is_read']
