from datetime import datetime

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.timezone import make_aware, now
from drf_spectacular.utils import extend_schema
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
    """
    Allow users to register by providing required fields.
    """
    queryset = get_user_model().objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """
    Log out the user by blacklisting the refresh token.
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer

    def post(self, request):
        """
        Blacklist the refresh token to log the user out.
        """
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=205)
        except Exception as e:
            return Response(status=400)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the current user's profile.
    """
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        """
        Get the current user object.
        """
        return self.request.user


class UserSearchView(generics.ListAPIView):
    """
    Search for users by username.
    """
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filter users by username.
        """
        queryset = super().get_queryset()
        username = self.request.query_params.get("username", None)
        if username:
            queryset = queryset.filter(username__icontains=username)
        return queryset


class FollowView(APIView):
    """
    Follow a user by username.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FollowSerializer

    def post(self, request, username):
        """
        Follow a user by username.
        """
        user_to_follow = get_object_or_404(get_user_model(), username=username)
        if request.user == user_to_follow:
            return Response({"error": "You cannot follow yourself."}, status=status.HTTP_400_BAD_REQUEST)

        follow, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
        if not created:
            return Response({"error": "You are already following this user."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"success": f"You are now following {username}."}, status=status.HTTP_201_CREATED)


class UnfollowView(APIView):
    """
    Unfollow a user by username.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    def post(self, request, username):
        """
        Unfollow a user by username.
        """
        user_to_unfollow = get_object_or_404(get_user_model(), username=username)
        follow = Follow.objects.filter(follower=request.user, following=user_to_unfollow)
        if follow.exists():
            follow.delete()
            return Response({"success": f"You have unfollowed {username}."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "You are not following this user."}, status=status.HTTP_400_BAD_REQUEST)


class FollowingListView(generics.ListAPIView):
    """
    Retrieve a list of users that the current user is following.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Get the list of users that the current user is following.
        """
        user = self.request.user
        following = Follow.objects.filter(follower=user).values_list('following', flat=True)
        return get_user_model().objects.filter(id__in=following)


class FollowersListView(generics.ListAPIView):
    """
    Retrieve a list of users that are following the current user.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Get the list of users that are following the current user.
        """
        user = self.request.user
        followers = Follow.objects.filter(following=user).values_list('follower', flat=True)
        return get_user_model().objects.filter(id__in=followers)


class FollowingPostsListView(generics.ListAPIView):
    """
    Retrieve a list of posts from users that the current user is following.
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get the list of posts from users that the current user is following.
        """
        following_users = Follow.objects.filter(follower=self.request.user).values_list('following', flat=True)
        return Post.objects.filter(user__in=following_users)


class PostViewSet(viewsets.ModelViewSet):
    """
    Perform CRUD operations on posts.
    """
    queryset = Post.objects.all().order_by("-created_at")
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        """
        Set the current user as the author of the post upon creation.
        """
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """
        Get posts filtered by the author's username if provided in query parameters.
        """
        if "username" in self.request.query_params:
            user = get_user_model().objects.get(username=self.request.query_params["username"])
            return Post.objects.filter(user=user)
        return Post.objects.filter(user=self.request.user)


class OwnPostsListView(generics.ListAPIView):
    """
    Retrieve a list of posts authored by the current user.
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get the list of posts authored by the current user.
        """
        return Post.objects.filter(user=self.request.user)


class SearchPostsView(generics.ListAPIView):
    """
    Search for posts containing specified criteria.
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get the list of posts filtered by search criteria in the content field.
        """
        queryset = Post.objects.all()
        search_criteria = self.request.query_params.get("search_criteria")
        if search_criteria:
            queryset = queryset.filter(content__icontains=search_criteria)
        return queryset


class LikeView(APIView):
    """
    Like or unlike a post.
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        """
        Like or unlike a post by providing the post ID.
        """
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
    """
    Perform CRUD operations on comments associated with posts.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Set the current user as the author of the comment upon creation.
        """
        post = Post.objects.get(id=self.kwargs['post_id'])
        serializer.save(user=self.request.user, post=post)
