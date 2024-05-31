from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import (
    generics,
    permissions,
    status,
    viewsets
)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
from api.tasks import create_scheduled_post

from api.models import (
    Follow,
    Post,
    Comment,
    Like
)
from api.serializers import (
    RegisterSerializer,
    UserSerializer,
    PostSerializer,
    CommentSerializer
)


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


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by("-created_at")
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        if "username" in self.request.query_params:
            user = (
                get_user_model().
                objects.get(
                    username=self.request.query_params["username"]
                )
            )
            return Post.objects.filter(user=user)
        return Post.objects.filter(user=self.request.user)


class LikeView(APIView):
    def post(self, request, post_id):
        post = Post.objects.get(id=post_id)
        like, created = Like.objects.get_or_create(
            user=request.user,
            post=post
        )
        if not created:
            like.delete()
            return Response(
                {"success": "Post unliked."},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {"success": "Post liked."},
            status=status.HTTP_201_CREATED
        )


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        post = Post.objects.get(id=self.kwargs['post_id'])
        serializer.save(user=self.request.user, post=post)


class SchedulePostView(APIView):
    def post(self, request):
        content = request.data.get("content")
        media = request.data.get("media")
        schedule_time = request.data.get("schedule_time")
        schedule_time = datetime.strptime(
            schedule_time,
            "%Y-%m-%d %H:%M:%S"
        )
        if schedule_time < timezone.now():
            return Response(
                {"error": "Schedule time must be in the future."},
                status=status.HTTP_400_BAD_REQUEST
            )
        delay = (schedule_time - timezone.now()).total_seconds()
        create_scheduled_post.apply_async(
            (request.user.id, content, media),
            countdown=delay
        )
        return Response(
            {"success": "Post scheduled successfully."},
            status=status.HTTP_201_CREATED
        )
