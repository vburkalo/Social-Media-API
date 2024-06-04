from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from api.views import (
    RegisterView,
    UserProfileView,
    FollowView,
    PostViewSet,
    LikeView,
    CommentViewSet,
    LogoutView,
    UserSearchView,
    FollowingListView,
    FollowersListView,
    UnfollowView,
    OwnPostsListView,
    FollowingPostsListView,
    SearchPostsView,
)

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
router.register("comments", CommentViewSet, basename="comment")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("search/", UserSearchView.as_view(), name="user-search"),
    path("follow/<str:username>/", FollowView.as_view(), name="follow"),
    path("unfollow/<str:username>/", UnfollowView.as_view(), name="unfollow"),
    path("following/", FollowingListView.as_view(), name="following-list"),
    path("followers/", FollowersListView.as_view(), name="followers-list"),
    path("posts/<int:post_id>/like/", LikeView.as_view(), name="like"),
    path("own-posts/", OwnPostsListView.as_view(), name="own-posts-list"),
    path("following-posts/", FollowingPostsListView.as_view(), name="following-posts-list"),
    path("search-posts/", SearchPostsView.as_view(), name="search-posts"),
]

urlpatterns += router.urls
