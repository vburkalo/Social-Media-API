from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Follow
from api.serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class FollowView(APIView):
    def post(self, request, username):
        try:
            user_to_follow = (
                get_user_model()
                .objects.get(username=username)
            )
            if request.user == user_to_follow:
                return Response(
                    {"error": "You cannot follow yourself."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow, created = Follow.objects.get_or_create(
                follower=request.user, following=user_to_follow
            )
            if not created:
                return Response(
                    {"error": "You are already following this user."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {"success": "You are now following {}.".format(username)},
                status=status.HTTP_201_CREATED
            )
        except get_user_model().DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, username):
        try:
            user_to_unfollow = (
                get_user_model()
                .objects.get(username=username)
            )
            follow = Follow.objects.filter(
                follower=request.user,
                following=user_to_unfollow
            )
            if follow.exists():
                follow.delete()
                return Response(
                    {"success": "You have unfollowed {}.".format(username)},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {"error": "You are not following this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except get_user_model().DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
