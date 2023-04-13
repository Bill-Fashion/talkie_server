from rest_framework import serializers

from .models import CustomUser, UserFriend


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('user_id', 'username', 'password',
                  'first_name', 'last_name', 'avatar')

    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = CustomUser(
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            avatar=validated_data.get('avatar', None)
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class SearchUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['user_id', 'username', 'first_name', 'last_name', 'avatar', 'date_joined']

class UserFriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFriend
        fields = ['id', 'user', 'friend', 'is_accepted']
        read_only_fields = ['id', 'is_accepted']
