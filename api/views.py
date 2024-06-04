from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
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


@extend_schema_view(
    post=extend_schema(
        summary="Register a new user",
        description="Allow users to register by providing required fields.",
        responses={
            201: UserSerializer,
            400: "Bad Request"
        }
    )
)
class RegisterView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema_view(
    post=extend_schema(
        summary="Log out user",
        description="Log out the user by blacklisting the refresh token.",
        request=None,
        responses={
            205: None,
            400: "Bad Request"
        }
    )
)
class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=205)
        except Exception as e:
            return Response(status=400)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve user profile",
        description="Retrieve the current user's profile.",
        responses={200: UserSerializer}
    ),
    put=extend_schema(
        summary="Update user profile",
        description="Update the current user's profile.",
        responses={200: UserSerializer}
    )
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        return self.request.user


@extend_schema_view(
    get=extend_schema(
        summary="Search users by username",
        description="Search for users by username.",
        parameters=[
            OpenApiParameter(name="username", description="Username to search for", required=False, type=str)
        ],
        responses={200: UserSerializer(many=True)}
    )
)
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


@extend_schema_view(
    post=extend_schema(
        summary="Follow a user",
        description="Follow a user by username.",
        parameters=[
            OpenApiParameter(name="username", description="Username of the user to follow", required=True, type=str)
        ],
        responses={
            201: "You are now following {username}.",
            400: "Bad Request"
        }
    )
)
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


@extend_schema_view(
    post=extend_schema(
        summary="Unfollow a user",
        description="Unfollow a user by username.",
        parameters=[
            OpenApiParameter(name="username", description="Username of the user to unfollow", required=True, type=str)
        ],
        responses={
            204: None,
            400: "Bad Request"
        }
    )
)
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


@extend_schema_view(
    get=extend_schema(
        summary="List following users",
        description="Retrieve a list of users that the current user is following.",
        responses={200: UserSerializer(many=True)}
    )
)
class FollowingListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        following = Follow.objects.filter(follower=user).values_list('following', flat=True)
        return get_user_model().objects.filter(id__in=following)


@extend_schema_view(
    get=extend_schema(
        summary="List followers",
        description="Retrieve a list of users that are following the current user.",
        responses={200: UserSerializer(many=True)}
    )
)
class FollowersListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        followers = Follow.objects.filter(following=user).values_list('follower', flat=True)
        return get_user_model().objects.filter(id__in=followers)


@extend_schema_view(
    get=extend_schema(
        summary="List posts from following users",
        description="Retrieve a list of posts from users that the current user is following.",
        responses={200: PostSerializer(many=True)}
    )
)
class FollowingPostsListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        following_users = Follow.objects.filter(follower=self.request.user).values_list('following', flat=True)
        return Post.objects.filter(user__in=following_users)


@extend_schema_view(
    list=extend_schema(
        summary="List posts",
        description="Retrieve a list of all posts or filter by author.",
        parameters=[
            OpenApiParameter(name="username", description="Username to filter posts by", required=False, type=str)
        ],
        responses={200: PostSerializer(many=True)}
    ),
    create=extend_schema(
        summary="Create a post",
        description="Create a new post.",
        responses={201: PostSerializer}
    ),
    retrieve=extend_schema(
        summary="Retrieve a post",
        description="Retrieve a specific post by ID.",
        responses={200: PostSerializer}
    ),
    update=extend_schema(
        summary="Update a post",
        description="Update a specific post by ID.",
        responses={200: PostSerializer}
    ),
    partial_update=extend_schema(
        summary="Partially update a post",
        description="Partially update a specific post by ID.",
        responses={200: PostSerializer}
    ),
    destroy=extend_schema(
        summary="Delete a post",
        description="Delete a specific post by ID.",
        responses={204: None}
    )
)
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by("-created_at")
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        if "username" in self.request.query_params:
            user = get_user_model().objects.get(username=self.request.query_params["username"])
            return Post.objects.filter(user=user)
        return Post.objects.filter(user=self.request.user)


@extend_schema_view(
    get=extend_schema(
        summary="List own posts",
        description="Retrieve a list of posts authored by the current user.",
        responses={200: PostSerializer(many=True)}
    )
)
class OwnPostsListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(user=self.request.user)


@extend_schema_view(
    get=extend_schema(
        summary="Search posts",
        description="Search for posts containing specified criteria.",
        parameters=[
            OpenApiParameter(name="search_criteria", description="Criteria to search posts by", required=False,
                             type=str)
        ],
        responses={200: PostSerializer(many=True)}
    )
)
class SearchPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Post.objects.all()
        search_criteria = self.request.query_params.get("search_criteria")
        if search_criteria:
            queryset = queryset.filter(content__icontains=search_criteria)
        return queryset


@extend_schema_view(
    post=extend_schema(
        summary="Like or unlike a post",
        description="Like or unlike a post by providing the post ID.",
        parameters=[
            OpenApiParameter(name="post_id", description="ID of the post to like or unlike", required=True, type=int)
        ],
        responses={
            201: "Post liked.",
            204: "Post unliked."
        }
    )
)
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


@extend_schema_view(
    list=extend_schema(
        summary="List comments",
        description="Retrieve a list of comments.",
        responses={200: CommentSerializer(many=True)}
    ),
    create=extend_schema(
        summary="Create a comment",
        description="Create a new comment on a post.",
        responses={201: CommentSerializer}
    ),
    retrieve=extend_schema(
        summary="Retrieve a comment",
        description="Retrieve a specific comment by ID.",
        responses={200: CommentSerializer}
    ),
    update=extend_schema(
        summary="Update a comment",
        description="Update a specific comment by ID.",
        responses={200: CommentSerializer}
    ),
    partial_update=extend_schema(
        summary="Partially update a comment",
        description="Partially update a specific comment by ID.",
        responses={200: CommentSerializer}
    ),
    destroy=extend_schema(
        summary="Delete a comment",
        description="Delete a specific comment by ID.",
        responses={204: None}
    )
)
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        post = Post.objects.get(id=self.kwargs['post_id'])
        serializer.save(user=self.request.user, post=post)
