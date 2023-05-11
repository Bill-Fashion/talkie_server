import uuid
from django.db import models
from accounts.models import CustomUser
from django.core.validators import MaxValueValidator, MinValueValidator


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(CustomUser)


class Message(models.Model):
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    sticker = models.URLField(blank=True, null=True)
    type = models.IntegerField(validators=[MaxValueValidator(9), MinValueValidator(0)], null=True, blank=True)
    status = models.CharField(max_length=10, choices=[
        ('not_sent', 'Not Sent'),
        ('not_seen', 'Not Seen'),
        ('seen', 'Seen'),
    ], default='not_sent')
    created_at = models.DateTimeField(auto_now_add=True)


