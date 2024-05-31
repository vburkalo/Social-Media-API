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
    FollowView, PostViewSet, LikeView, CommentViewSet,
)

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("follow/<str:username>", FollowView.as_view(), name="follow"),
    path("posts/<int:post_id>/like/", LikeView.as_view(), name="like"),
    path(
        "posts/<int:post_id>/comments/",
        CommentViewSet.as_view(
            {"get": "list", "post": "create"}
        ),
        name="comments"),
]

urlpatterns += router.urls
