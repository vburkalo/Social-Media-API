from django.test import TestCase
from django.contrib.auth import get_user_model
from api.models import Follow, Post, Like, Comment
from api.serializers import (
    UserSerializer,
    RegisterSerializer,
    FollowSerializer,
    PostSerializer,
    LikeSerializer,
    CommentSerializer,
)


class UserSerializerTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123",
            email="testuser@example.com",
            bio="This is a bio",
        )

    def test_user_serializer(self):
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        self.assertEqual(data["username"], self.user.username)
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["bio"], self.user.bio)
        self.assertEqual(data["followers_count"], 0)
        self.assertEqual(data["following_count"], 0)


class RegisterSerializerTest(TestCase):

    def test_register_serializer(self):
        user_data = {
            "username": "newuser",
            "password": "newpassword123",
            "email": "newuser@example.com",
        }
        serializer = RegisterSerializer(data=user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.check_password("newpassword123"))


class FollowSerializerTest(TestCase):

    def setUp(self):
        self.user1 = get_user_model().objects.create_user(
            username="user1", password="testpass123"
        )
        self.user2 = get_user_model().objects.create_user(
            username="user2", password="testpass123"
        )
        self.follow = Follow.objects.create(follower=self.user1, following=self.user2)

    def test_follow_serializer(self):
        serializer = FollowSerializer(instance=self.follow)
        data = serializer.data
        self.assertEqual(data["follower"], self.follow.follower.id)
        self.assertEqual(data["following"], self.follow.following.id)


class PostSerializerTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="user", password="testpass123"
        )
        self.post = Post.objects.create(user=self.user, content="This is a test post")

    def test_post_serializer(self):
        serializer = PostSerializer(instance=self.post)
        data = serializer.data
        self.assertEqual(data["user"]["username"], self.user.username)
        self.assertEqual(data["content"], self.post.content)
        self.assertTrue(data["created_at"])
        self.assertTrue(data["updated_at"])


class LikeSerializerTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="user", password="testpass123"
        )
        self.post = Post.objects.create(user=self.user, content="This is a test post")
        self.like = Like.objects.create(user=self.user, post=self.post)

    def test_like_serializer(self):
        serializer = LikeSerializer(instance=self.like)
        data = serializer.data
        self.assertEqual(data["user"], self.like.user.id)
        self.assertEqual(data["post"], self.like.post.id)


class CommentSerializerTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="user", password="testpass123"
        )
        self.post = Post.objects.create(user=self.user, content="This is a test post")
        self.comment = Comment.objects.create(
            user=self.user, post=self.post, content="This is a comment"
        )

    def test_comment_serializer(self):
        serializer = CommentSerializer(instance=self.comment)
        data = serializer.data
        self.assertEqual(data["user"]["username"], self.user.username)
        self.assertEqual(data["post"], self.comment.post.id)
        self.assertEqual(data["content"], self.comment.content)
        self.assertTrue(data["created_at"])
