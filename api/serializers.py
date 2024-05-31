from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.models import Follow


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email", "bio", "profile_picture")


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("username", "password", "email")
        extra_kwargs = {"password": {"write_only": True, "min_length": 8}}

    def create(self, validated_data):
        user = get_user_model().objects.create_user(**validated_data)
        return user


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ("id", "follower", "following", "created_at")
