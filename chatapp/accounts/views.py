from django.shortcuts import get_object_or_404, render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.serializers import UserFriendSerializer, UserSerializer, SearchUserSerializer
from django.contrib.auth import authenticate, get_user_model
from oauth2_provider.models import AccessToken, RefreshToken, Application
from oauthlib.common import generate_token
from datetime import datetime, timedelta
from django.conf import settings
from oauth2_provider.settings import oauth2_settings
from .models import CustomUser, UserFriend
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
import base64
from django.core.files.base import ContentFile


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'Please provide both username and password'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(
            request=request, username=username, password=password)
        if not user:
            return Response({'error': 'Wrong username or password'}, status=status.HTTP_401_UNAUTHORIZED)

        app, created = Application.objects.get_or_create(
            name='Authentication API',
            user=user,
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_PASSWORD,
        )

        AccessToken.objects.filter(user=user, application=app).delete()
        RefreshToken.objects.filter(user=user, application=app).delete()

        access_token = AccessToken.objects.create(
            user=user,
            application=app,
            token=generate_token(),
            expires=datetime.now() +
            timedelta(
                seconds=settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS']),
            scope='',
        )
        refresh_token = RefreshToken.objects.create(
            user=user,
            application=app,
            token=generate_token(),
            access_token=access_token,
        )
        data = {
            'access_token': access_token.token,
            'refresh_token': refresh_token.token,
            'token_type': 'Bearer',
            'expires_in': oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
            'user_id': user.pk
        }

        return Response(data)


class TokenDeleteView(APIView):
    def post(self, request):
        # Check if the user exists
        User = get_user_model()
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_401_UNAUTHORIZED)

        # Delete the access token and refresh token for the user
        AccessToken.objects.filter(user=user).delete()
        RefreshToken.objects.filter(user=user).delete()
        return Response({"message": "Tokens deleted successfully."}, status=status.HTTP_200_OK)


class UserSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('query', '').split(' ')
        first_name = query[0] if len(query) > 0 else ''
        last_name = query[1] if len(query) > 1 else ''

        users = CustomUser.objects.filter(
            Q(first_name__icontains=first_name) | Q(
                last_name__icontains=last_name)
        )
        serializer = SearchUserSerializer(users, many=True)

        return Response(serializer.data)

class UserInfo(APIView):
    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(user_id=user_id)
        except ObjectDoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)

        serializer = SearchUserSerializer(user)
        return Response(serializer.data)
    
class UpdateUser(APIView):
    def patch(self, request):
        userId = request.data.get('user_id')
        user = CustomUser.objects.get(user_id=userId)
        # Get the data from the request
        data = request.data

        # Update the user object with the new data
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'avatar' in data:
            user.avatar = data['avatar']
        
        # Save the changes to the user object
        user.save()

        # Return the updated user object
        serializer = SearchUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class SendFriendRequest(APIView):
    def post(self, request):
        senderId = request.data.get("sender_id")
        receiverId = request.data.get("receiver_id")
        sender = get_object_or_404(CustomUser, user_id=senderId)
        receiver = get_object_or_404(CustomUser, user_id=receiverId)

        if UserFriend.objects.filter(user=sender, friend=receiver).exists() or \
           UserFriend.objects.filter(user=receiver, friend=sender).exists():
            return Response({'message': 'Friend request already sent or accepted'},
                            status=status.HTTP_400_BAD_REQUEST)
        
        friendship = UserFriend(user=sender, friend=receiver)
        friendship.save()
        serializer = UserFriendSerializer(friendship)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class GetRelationshipStatus(APIView):
    def post(self, request):
        userId = request.data.get("user_id")
        friendId = request.data.get("friend_id")
        user = get_object_or_404(CustomUser, user_id=userId)
        friend = get_object_or_404(CustomUser, user_id=friendId)

        # test1 = UserFriend.objects.filter(user=user, friend=friend).exists()
        # print(test1)
        # test2 = UserFriend.objects.filter(user=friend, friend=user).exists()
        # print(test2)
        if UserFriend.objects.filter(user=user, friend=friend).exists():
            # print("Inside 1")
            relationship = UserFriend.objects.filter(user=user, friend=friend).first()
            # print(relationship)
            serializer = UserFriendSerializer(relationship)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        if UserFriend.objects.filter(user=friend, friend=user).exists():
            print("Inside 2")
            relationship = UserFriend.objects.filter(user=friend, friend=user).first()
            print(relationship)
            serializer = UserFriendSerializer(relationship)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        else: return Response(status=status.HTTP_404_NOT_FOUND)

class FriendRequests(APIView):
    def get(self, request, user_id):
        user = CustomUser.objects.get(user_id=user_id)
        data=[]

        if UserFriend.objects.filter(friend=user, is_accepted=False).exists():
            requests = UserFriend.objects.filter(friend=user, is_accepted=False)
            for request in requests:
                userRequests = CustomUser.objects.get(user_id=request.user.user_id)
                requestDetails = {
                    'id': request.id,
                    'user': SearchUserSerializer(userRequests).data
                }
                data.append(requestDetails)

        return Response(data, status=status.HTTP_200_OK)

class AcceptFriendRequest(APIView):
    def put(self, request, request_id):
        try:
            friendship = UserFriend.objects.get(id=request_id)
        except ObjectDoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)
        friendship.is_accepted = True
        friendship.save()
        serializer = UserFriendSerializer(friendship)

        return Response(serializer.data, status=status.HTTP_200_OK)    

class UserFriendList(APIView):
    def get(self, request, user_id):
        user = CustomUser.objects.get(user_id=user_id)
        usersFriends = []
        
        if UserFriend.objects.filter(user=user, is_accepted=True).exists():
            friend_ids = UserFriend.objects.filter(user=user, is_accepted=True).values_list('friend', flat=True)
            for friend_id in friend_ids:
                friends = CustomUser.objects.filter(user_id=friend_id)
                usersFriends.extend(friends)
        if UserFriend.objects.filter(friend=user, is_accepted=True).exists():
            friend_ids = UserFriend.objects.filter(friend=user, is_accepted=True).values_list('user', flat=True)
            for friend_id in friend_ids:
                friends = CustomUser.objects.filter(user_id=friend_id)
                usersFriends.extend(friends)
        
        serializer = SearchUserSerializer(usersFriends, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class DeleteUserFriendRequest(APIView):
    def delete(self, request, id):
        try:
            friendRequest = UserFriend.objects.get(id=id)
            friendRequest.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserFriend.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)