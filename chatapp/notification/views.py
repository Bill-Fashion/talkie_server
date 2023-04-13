from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.models import CustomUser, UserDevice
from django.shortcuts import get_object_or_404
from .firebase import push_notification

class SaveToken(APIView):
    def post(self, request):
        userId = request.data.get("user_id")
        token = request.data.get("token")
        user = get_object_or_404(CustomUser, user_id=userId)
        if not UserDevice.objects.filter(device_token=token, user=user).exists():
            device = UserDevice.objects.create(user=user, device_token=token)
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_302_FOUND)

class PushNotification(APIView):
    def post(self, request):
        senderId = request.data.get("sender_id")
        roomId = request.data.get("room_id")
        # push_notification(senderId=senderId, roomId=roomId)
        return Response({"msg": "Success"}, status=status.HTTP_200_OK)
