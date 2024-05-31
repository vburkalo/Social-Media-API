from celery import shared_task
from django.utils import timezone
from api.models import Post, CustomUser


@shared_task
def create_scheduled_post(user_id, content, media=None):
    user = CustomUser.objects.get(id=user_id)
    Post.objects.create(user=user, content=content, media=media)
