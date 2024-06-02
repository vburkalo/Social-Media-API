from datetime import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
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

from api.models import (
    Follow,
    Post,
    Comment,
    Like
)
from api.permissions import IsOwnerOrReadOnly
from api.serializers import (
    RegisterSerializer,
    UserSerializer,
    PostSerializer,
    CommentSerializer, FollowSerializer
)
from api.tasks import create_scheduled_post


class RegisterView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=205)
        except Exception as e:
            return Response(status=400)


class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        return self.request.user


class UserSearchView(generics.ListAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        username = self.request.query_params.get("username", None)
        if username:
            queryset = queryset.filter(username__icontains=username)
        return queryset


class FollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FollowSerializer

    def post(self, request, username):
        user_to_follow = get_object_or_404(get_user_model(), username=username)
        if request.user == user_to_follow:
            return Response({"error": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        follow, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
        if not created:
            return Response({"error": "You are already following this user."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": f"You are now following {username}."}, status=status.HTTP_201_CREATED)


class UnfollowView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    def post(self, request, username):
        user_to_unfollow = get_object_or_404(get_user_model(), username=username)
        follow = Follow.objects.filter(follower=request.user, following=user_to_unfollow)
        if follow.exists():
            follow.delete()
            return Response({"success": f"You have unfollowed {username}."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "You are not following this user."}, status=status.HTTP_400_BAD_REQUEST)


class FollowingListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        following = Follow.objects.filter(follower=user).values_list('following', flat=True)
        return get_user_model().objects.filter(id__in=following)


class FollowersListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        followers = Follow.objects.filter(following=user).values_list('follower', flat=True)
        return get_user_model().objects.filter(id__in=followers)


class FollowingPostsListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        following_users = Follow.objects.filter(follower=self.request.user).values_list('following', flat=True)
        return Post.objects.filter(user__in=following_users)


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


class OwnPostsListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)


class SearchPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Post.objects.all()
        search_criteria = self.request.query_params.get("search_criteria")
        if search_criteria:
            queryset = queryset.filter(content__icontains=search_criteria)
        return queryset


class LikeView(APIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

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
