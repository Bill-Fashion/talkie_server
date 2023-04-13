from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404, render
from .models import *
from .serializers import RoomSerializer
from django.db.models import Max, OuterRef, Subquery
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from operator import itemgetter


def lobby(request):
    return render(request, 'chat/lobby.html')


class RoomCreateView(generics.CreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def create(self, request, *args, **kwargs):
        user_ids = request.data.get('user_ids', [])
        members = CustomUser.objects.filter(user_id__in=user_ids)
        room = Room.objects.create(name=request.data.get('name', ''))
        room.members.set(members)
        serializer = self.get_serializer(room)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class GetRoom(APIView):
    def get(self, request, user_id1, user_id2):
        # Get the users
        user1 = get_object_or_404(CustomUser, user_id=user_id1)
        user2 = get_object_or_404(CustomUser, user_id=user_id2)

        # Get the rooms that both users are members of
        rooms = Room.objects.filter(members=user1).filter(members=user2)

        # Return the first room found (if any)
        if rooms.exists():
            room = rooms.first()
            data = {
                'id': room.id,
                'name': room.name,
                'members': [user.user_id for user in room.members.all()],
            }
            return Response(data)
        else:
            return Response({'detail': 'No room found for the provided users.'}, status=404)
        

class GetRoomsInfo(APIView):
    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(user_id=user_id)
        except ObjectDoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)
        # Retrieves all the rooms that the user is a member of
        rooms = user.room_set.all()
        data = []

        for room in rooms:
            # Check if the room has at least one message
            if not room.messages.exists():
                continue

            # Retrieves the latest message in the room
            last_message = room.messages.all().aggregate(Max('created_at'))
            last_message = last_message['created_at__max']
            if last_message:
                last_message = Message.objects.filter(created_at=last_message, room=room).first()

            try:
                other_member = room.members.exclude(user_id=user_id).first()
                other_member_info = {
                    'id': other_member.user_id,
                    'name': other_member.first_name + " " + other_member.last_name,
                    'avatar': other_member.avatar,
                }
            except ObjectDoesNotExist:
                other_member_info = {}

            room_info = {
                'id': room.id,
                'name': room.name,
                'last_message': {
                    'text': last_message.text if last_message else '',
                    'sender': last_message.sender.user_id if last_message else '',
                    'created_at': last_message.created_at if last_message else '',
                },
                'other_member': other_member_info,
            }

            # print(room_info)
            data.append(room_info)
        print(data)
        data = sorted(data, key=lambda x: x['last_message']['created_at'], reverse=True)
        return Response(data)

class GetLatestMessages(APIView):
    def get(self, request, room_id):
    # Get the room by its ID
        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({'error': 'Room does not exist'})

        # Get the 20 latest messages from the room
        messages = Message.objects.filter(room=room).order_by('-created_at')[:20]

        # Encrypt the message content using Fernet
        # key = Fernet.generate_key()
        # f = Fernet(key)
        # for message in messages:
        #     if message.text:
        #         encrypted_text = f.encrypt(message.text.encode())
        #         message.text = encrypted_text.decode()

        # Serialize the messages and return the response
        data = [{
                'msg_type': message.type,
                'content': message.text if message.type==0 else message.image.url if message.type==1 else message.sticker,
                'sender_id': message.sender_id,
                'created_at': message.created_at} for message in messages]
        return Response({'data': data})
