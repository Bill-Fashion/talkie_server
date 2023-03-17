import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError(_('The Username field must be set'))
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class CustomUser(AbstractUser):
    user_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    avatar = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    @property
    def refresh_tokens(self):
        return self.refreshtoken_set.all()

    def __str__(self):
        return self.username


class UserSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
    session_data = models.TextField()
    expire_date = models.DateTimeField()


class UserDevice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255)
    device_token = models.CharField(max_length=255)


class UserFriend(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='user')
    friend = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='friend')
    is_accepted = models.BooleanField(default=False)
