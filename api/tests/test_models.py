from django.contrib.auth import get_user_model
from django.test import TestCase

from api.models import Follow, Post, Like, Comment


class CustomUserModelTest(TestCase):

    def test_create_user_with_bio(self):
        user = get_user_model().objects.create_user(
            username="testuser", password="testpass123", bio="This is a bio"
        )
        self.assertEqual(user.bio, "This is a bio")

    def test_create_user_without_bio(self):
        user = get_user_model().objects.create_user(
            username="testuser2", password="testpass123"
        )
        self.assertEqual(user.bio, None)


class FollowModelTest(TestCase):

    def setUp(self):
        self.user1 = get_user_model().objects.create_user(
            username="user1", password="testpass123"
        )
        self.user2 = get_user_model().objects.create_user(
            username="user2", password="testpass123"
        )

    def test_follow_user(self):
        follow = Follow.objects.create(follower=self.user1, following=self.user2)
        self.assertEqual(follow.follower, self.user1)
        self.assertEqual(follow.following, self.user2)

    def test_unique_follow(self):
        Follow.objects.create(follower=self.user1, following=self.user2)
        with self.assertRaises(Exception):
            Follow.objects.create(follower=self.user1, following=self.user2)


class PostModelTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="user", password="testpass123"
        )

    def test_create_post(self):
        post = Post.objects.create(user=self.user, content="This is a test post")
        self.assertEqual(post.content, "This is a test post")
        self.assertEqual(post.user, self.user)
        self.assertTrue(post.created_at)
        self.assertTrue(post.updated_at)

    def test_post_str(self):
        post = Post.objects.create(user=self.user, content="This is a test post")
        self.assertEqual(str(post), "This is a test post"[:20])


class LikeModelTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="user", password="testpass123"
        )
        self.post = Post.objects.create(user=self.user, content="This is a test post")

    def test_create_like(self):
        like = Like.objects.create(user=self.user, post=self.post)
        self.assertEqual(like.user, self.user)
        self.assertEqual(like.post, self.post)

    def test_unique_like(self):
        Like.objects.create(user=self.user, post=self.post)
        with self.assertRaises(Exception):
            Like.objects.create(user=self.user, post=self.post)


class CommentModelTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="user", password="testpass123"
        )
        self.post = Post.objects.create(user=self.user, content="This is a test post")

    def test_create_comment(self):
        comment = Comment.objects.create(
            user=self.user, post=self.post, content="This is a comment"
        )
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.content, "This is a comment")
        self.assertTrue(comment.created_at)
