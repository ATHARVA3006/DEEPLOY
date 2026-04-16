from django.db import models
from django.contrib.auth.models import User
import uuid
import os


class UserProfile(models.Model):
    GENDER_CHOICES = [('male','Male'),('female','Female'),('other','Other'),('prefer_not','Prefer not to say')]

    user         = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio          = models.TextField(blank=True)
    avatar       = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone        = models.CharField(max_length=20, blank=True)
    gender       = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    date_of_birth= models.DateField(null=True, blank=True)
    website      = models.URLField(blank=True)
    location     = models.CharField(max_length=100, blank=True)
    company      = models.CharField(max_length=100, blank=True)
    github       = models.URLField(blank=True)
    twitter      = models.URLField(blank=True)
    linkedin     = models.URLField(blank=True)
    is_verified  = models.BooleanField(default=False)
    is_banned    = models.BooleanField(default=False)
    ban_reason   = models.TextField(blank=True)
    last_seen    = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Subscription(models.Model):
    PLAN_CHOICES = [('free','Free'),('pro','Pro'),('premium','Premium')]

    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan          = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    custom_domain = models.CharField(max_length=200, blank=True, null=True, unique=True)
    started_at    = models.DateTimeField(auto_now_add=True)
    expires_at    = models.DateTimeField(null=True, blank=True)
    is_active     = models.BooleanField(default=True)
    storage_used  = models.BigIntegerField(default=0)
    storage_limit = models.BigIntegerField(default=524288000)  # 500MB

    def __str__(self):
        return f"{self.user.username} - {self.plan}"

    def can_use_custom_domain(self):
        return self.plan in ['pro', 'premium'] and self.is_active

    def storage_used_mb(self):
        return round(self.storage_used / 1024 / 1024, 2)


class Folder(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    is_public   = models.BooleanField(default=True)
    visits      = models.IntegerField(default=0)
    custom_slug = models.SlugField(max_length=100, blank=True, null=True)
    tags        = models.CharField(max_length=300, blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_share_link(self):
        return f"/folder/{self.id}/"

    def total_size(self):
        return self.files.aggregate(models.Sum('size'))['size__sum'] or 0


class File(models.Model):
    folder      = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='files')
    name        = models.CharField(max_length=255)
    file        = models.FileField(upload_to='uploads/')
    path        = models.CharField(max_length=500, default='/')
    file_type   = models.CharField(max_length=50)
    size        = models.BigIntegerField(default=0)
    downloads   = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['path', 'name']

    def __str__(self):
        return f"{self.path}{self.name}"

    def get_extension(self):
        return os.path.splitext(self.name)[1].lower()

    def is_image(self):
        return self.get_extension() in ['.jpg','.jpeg','.png','.gif','.bmp','.svg','.webp','.ico','.tiff','.avif']

    def is_text(self):
        return self.get_extension() in [
            '.txt','.py','.js','.ts','.jsx','.tsx','.html','.htm','.css','.scss','.sass',
            '.json','.xml','.md','.markdown','.yaml','.yml','.toml','.ini','.env',
            '.java','.cpp','.c','.h','.cs','.go','.rs','.php','.rb','.swift',
            '.sh','.bash','.zsh','.ps1','.bat','.sql','.graphql','.vue','.svelte',
            '.dockerfile','.gitignore','.htaccess','.nginx','.conf',
        ]

    def is_video(self):
        return self.get_extension() in ['.mp4','.webm','.ogg','.mov','.avi','.mkv']

    def is_audio(self):
        return self.get_extension() in ['.mp3','.wav','.ogg','.flac','.aac','.m4a']

    def is_pdf(self):
        return self.get_extension() == '.pdf'

    def is_archive(self):
        return self.get_extension() in ['.zip','.tar','.gz','.rar','.7z']

    def size_kb(self):
        return round(self.size / 1024, 2)


class UserLink(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='links')
    title      = models.CharField(max_length=100)
    url        = models.URLField(max_length=500)
    icon       = models.CharField(max_length=50, default='🔗')
    created_at = models.DateTimeField(auto_now_add=True)
    order      = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login','Login'), ('logout','Logout'), ('register','Register'),
        ('upload','Upload'), ('delete','Delete'), ('view','View'),
        ('download','Download'), ('share','Share'), ('update','Update'),
    ]
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action     = models.CharField(max_length=20, choices=ACTION_CHOICES)
    detail     = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.created_at}"


class Notification(models.Model):
    TYPE_CHOICES = [('info','Info'),('success','Success'),('warning','Warning'),('error','Error')]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_extras(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        Subscription.objects.get_or_create(user=instance)
