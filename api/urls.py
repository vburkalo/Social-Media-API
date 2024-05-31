from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from api.views import (
    RegisterView,
    UserProfileView,
    FollowView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token"),
    path("token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("follow/<str:username>", FollowView.as_view(), name="follow"),
]
