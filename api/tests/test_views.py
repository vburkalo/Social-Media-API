from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import AccessToken

from api.models import Follow, Post, Like, Comment

User = get_user_model()


class RegisterViewTestCase(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")

    def test_register_user(self):
        data = {
            "username": "test_user",
            "email": "test@example.com",
            "password": "testpassword123",
        }

        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(get_user_model().objects.get().username, "test_user")


class UserProfileViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_profile(self):
        url = reverse("profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorized_access(self):
        self.client.logout()
        url = reverse("profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserSearchViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create(username="user1", email="user1@example.com")
        self.user2 = User.objects.create(username="user2", email="user2@example.com")
        self.client.force_authenticate(user=self.user1)

    def test_search_user_by_username(self):
        response = self.client.get(reverse("user-search") + "?username=user1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], "user1")

    def test_search_user_no_username(self):
        response = self.client.get(reverse("user-search"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_search_user_case_insensitive(self):
        response = self.client.get(reverse("user-search") + "?username=USER1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], "user1")

    def test_search_user_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("user-search") + "?username=user1")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class FollowViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = get_user_model().objects.create(
            username="user1", email="user1@example.com"
        )
        self.user2 = get_user_model().objects.create(
            username="user2", email="user2@example.com"
        )
        self.client.force_authenticate(user=self.user1)

    def test_follow_user(self):
        url = reverse("follow", kwargs={"username": self.user2.username})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_follow_self(self):
        url = reverse("follow", kwargs={"username": self.user1.username})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "You cannot follow yourself.")
        self.assertFalse(
            Follow.objects.filter(follower=self.user1, following=self.user1).exists()
        )

    def test_follow_already_followed(self):
        Follow.objects.create(follower=self.user1, following=self.user2)
        url = reverse("follow", kwargs={"username": self.user2.username})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "You are already following this user.")


class UnfollowViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = get_user_model().objects.create(
            username="user1", email="user1@example.com"
        )
        self.user2 = get_user_model().objects.create(
            username="user2", email="user2@example.com"
        )
        self.follow = Follow.objects.create(follower=self.user1, following=self.user2)
        self.client.force_authenticate(user=self.user1)

    def test_unfollow_user(self):
        url = reverse("unfollow", kwargs={"username": self.user2.username})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_unfollow_not_followed(self):
        self.follow.delete()
        url = reverse("unfollow", kwargs={"username": self.user2.username})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "You are not following this user.")


class FollowingListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = get_user_model().objects.create(
            username="user1", email="user1@example.com"
        )
        self.user2 = get_user_model().objects.create(
            username="user2", email="user2@example.com"
        )
        self.user3 = get_user_model().objects.create(
            username="user3", email="user3@example.com"
        )

        Follow.objects.create(follower=self.user1, following=self.user2)
        Follow.objects.create(follower=self.user1, following=self.user3)

        self.client.force_authenticate(user=self.user1)

    def test_get_following_list(self):
        url = reverse("following-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["username"], self.user2.username)
        self.assertEqual(response.data[1]["username"], self.user3.username)

    def test_get_following_list_unauthenticated(self):
        self.client.logout()
        url = reverse("following-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PostViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = get_user_model().objects.create(
            username="user1", email="user1@example.com"
        )
        self.user2 = get_user_model().objects.create(
            username="user2", email="user2@example.com"
        )
        self.post1 = Post.objects.create(user=self.user1, content="Post 1")
        self.post2 = Post.objects.create(user=self.user2, content="Post 2")

    def test_list_posts_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse("post-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["content"], "Post 1")

    def test_list_posts_unauthenticated(self):
        url = reverse("post-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_post_authenticated(self):
        self.client.force_authenticate(user=self.user1)
        url = reverse("post-list")
        data = {"content": "New post"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 3)
        new_post = Post.objects.latest("created_at")
        self.assertEqual(new_post.user, self.user1)
        self.assertEqual(new_post.content, "New post")

    def test_create_post_unauthenticated(self):
        url = reverse("post-list")
        data = {"content": "New post"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 2)


class OwnPostsListViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="test_user", email="test@example.com", password="testpass"
        )
        self.post = Post.objects.create(user=self.user, content="Test content")

        self.token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_own_posts_list_authenticated(self):
        url = reverse("own-posts-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["content"], "Test content")

    def test_own_posts_list_unauthenticated(self):
        self.client.credentials()
        url = reverse("own-posts-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SearchPostsViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="test_user", email="test@example.com", password="testpass"
        )
        self.post1 = Post.objects.create(user=self.user, content="Test content 1")
        self.post2 = Post.objects.create(user=self.user, content="Another content")
        self.post3 = Post.objects.create(user=self.user, content="Something different")
        self.access_token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_search_posts_with_criteria(self):
        url = reverse("search-posts")
        search_criteria = "Test"
        response = self.client.get(url, {"search_criteria": search_criteria})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["content"], "Test content 1")

    def test_search_posts_without_criteria(self):
        url = reverse("search-posts")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)


class LikeViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="test_user", email="test@example.com", password="testpass"
        )
        self.post = Post.objects.create(user=self.user, content="Test content")
        self.like_url = reverse("like", kwargs={"post_id": self.post.id})

    def test_like_post_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.like_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Like.objects.filter(user=self.user, post=self.post).exists())

    def test_like_post_unauthenticated(self):
        response = self.client.post(self.like_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unlike_post_authenticated(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.like_url)

        # Then, unlike the post
        response = self.client.post(self.like_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Like.objects.filter(user=self.user, post=self.post).exists())

    def test_unlike_post_unauthenticated(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(self.like_url)

        self.client.logout()
        response = self.client.post(self.like_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CommentViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="test_user", email="test@example.com", password="testpass"
        )
        self.post = Post.objects.create(user=self.user, content="Test post content")
        self.comment_data = {"content": "Test comment content"}
        self.comment_url = reverse("comment-list")
        self.client.force_authenticate(user=self.user)

    def test_create_comment(self):
        url = reverse("comment-list")
        response = self.client.post(
            url, {"post": self.post.id, "content": "Test comment content"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.get().content, "Test comment content")

    def test_get_comments(self):
        Comment.objects.create(user=self.user, post=self.post, content="Comment 1")
        Comment.objects.create(user=self.user, post=self.post, content="Comment 2")

        url_with_post_id = f"{self.comment_url}?post_id={self.post.id}"
        response = self.client.get(url_with_post_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
