from chat.managers import ThreadManager
from django.db import models

from django.contrib.auth.models import BaseUserManager, AbstractUser

import uuid

from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django.conf import settings


class UserManager(BaseUserManager):
    """
        Not a model but a manager that helps define our custom user model to remove
        username as a required field  or even a None field
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""

        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)



class User(AbstractUser):

    # STATUS = (
    #     ('online', 'On-line'),
    #     ('offline', 'off-line')
    # )
    
    email = models.EmailField(null=True, blank=True, unique=True)
    username = models.CharField(max_length=25, null=True, blank=True, unique=True)
    first_name = models.CharField(max_length=200, null=True)
    last_name = models.CharField(max_length=200, null=True)
    online = models.IntegerField(default=0, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username',] # Email & Password are required by default.

    objects = UserManager()

    def __str__(self):
        return str(self.username)








User = settings.AUTH_USER_MODEL

class TrackingModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Thread(TrackingModel):
    THREAD_TYPE = (
        ('personal', 'Personal'),
        ('group', 'Group')
    )

    name = models.CharField(max_length=50, null=True, blank=True)
    thread_type = models.CharField(max_length=15, choices=THREAD_TYPE, default='personal')
    users = models.ManyToManyField(User)

    objects = ThreadManager()

    def __str__(self) -> str:
        if self.thread_type == 'personal' and self.users.count() == 2:
            return f'{self.users.first()} and {self.users.last()}'
        return f'{self.name}'

class Message(TrackingModel):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=False, null=False)
    image = models.ImageField(upload_to='message-image/', blank=True, null=True)
    audio_file = models.FileField(upload_to='audio-file/', blank=True, null=True)

    def __str__(self) -> str:
        return f'From <Thread - {self.thread}>'


class Notification(models.Model):
    notification_user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_chat = models.ForeignKey(Message, on_delete=models.CASCADE)
    notification_read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.id}' 


# send notification to consumer
@receiver(post_save, sender=Message)
def update_stock(sender, instance, created, **kwargs):
    if created:
        if instance.sender:
            other_user = instance.thread.users.exclude(id=instance.sender.id).first()
            if other_user:
                notify_obj = Notification.objects.create(notification_user=instance.sender, notification_chat=instance)
                notify_qs = Notification.objects.filter(notification_user=instance.sender, notification_read=False).count()
                if  notify_qs:
                    async_to_sync(get_channel_layer().group_send)(
                        f"notify_room_for_user_{other_user.id}",
                        {
                            'type': 'notification',
                            'message': f"New message from {instance.sender.username}",
                            'message_counter': f"{notify_qs}",
                            'sender': instance.sender.username
                        }
                    ) 



     