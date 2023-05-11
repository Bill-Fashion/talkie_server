import datetime
import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from accounts.models import CustomUser, UserDevice
from chat.serializers import MessageSerializer
from django.core import serializers
from .models import Room, Message
from enum import Enum
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
import base64
from django.core.files.base import ContentFile
from notification.firebase import push_notification

class MessageType(Enum):
    TEXT = 'text'
    IMAGE = 'image'
    STICKER = 'sticker'

@database_sync_to_async
def get_room(room_id):
    return Room.objects.get(id=room_id)

@database_sync_to_async
def get_user(sender_id):
    return CustomUser.objects.get(user_id=sender_id)

@database_sync_to_async
def get_user_device(other_member):
    devices = UserDevice.objects.filter(user=other_member).values_list('device_token', flat=True)
    return [device for device in devices]

@database_sync_to_async
def get_other_members(room, sender_id):
    return room.members.exclude(user_id=sender_id).first()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = str(
            uuid.UUID(self.scope['url_route']['kwargs']['room_id']))
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['msg_type']       
        sender_id = text_data_json['sender_id']
        room_id = text_data_json['room_id']
        room = await get_room(room_id)
        sender = await get_user(sender_id)
    
        if message_type == 0:
            content = text_data_json['content']
            message = await self.save_message(message_type, room, sender, content)
        elif message_type == 1:
            content = text_data_json.get('content', None)
            message = await self.save_message(message_type, room, sender, content)
        elif message_type == 2:
            content = text_data_json.get('content', None)
            message = await self.save_message(message_type, room, sender, content)
        
        other_member = await get_other_members(room, sender_id)
        # print(other_members.user_id)
        registration_tokens = await get_user_device(other_member)
        
        # = [registration_token for registration_token in registration_devices]
        push_notification(registration_tokens=registration_tokens, senderId=sender_id, roomId=room_id)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'msg_type': message_type,
                'content': content,
                'sender_id': sender_id,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        
        msg_type = event['msg_type']
        content = event['content']
        sender_id = event['sender_id']
        created_at = event['created_at']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'msg_type': msg_type,
            'content': content,
            'sender_id': sender_id,
            'created_at': created_at
        }))
        
    @sync_to_async
    def save_message(self, message_type, room, sender, content):
        
        if message_type==0:
            return Message.objects.create(type=message_type, room=room, sender=sender, text=content, status='not_sent')
        elif message_type==1:
            return Message.objects.create(type=message_type, room=room, sender=sender, image_url=content, status='not_sent')
        else:
            return Message.objects.create(type=message_type, room=room, sender=sender, sticker=content, status='not_sent')
