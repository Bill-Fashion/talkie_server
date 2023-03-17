
from django.shortcuts import get_object_or_404, render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.serializers import UserSerializer, SearchUserSerializer
from django.contrib.auth import authenticate, get_user_model
from oauth2_provider.models import AccessToken, RefreshToken, Application
from oauthlib.common import generate_token
from datetime import datetime, timedelta
from django.conf import settings
from oauth2_provider.settings import oauth2_settings
from .models import CustomUser
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist


class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    # Initialize a mutex

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

        # Delete any existing access tokens and refresh tokens for this user and application
        AccessToken.objects.filter(user=user, application=app).delete()
        RefreshToken.objects.filter(user=user, application=app).delete()

        # Generate new access token and refresh token
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