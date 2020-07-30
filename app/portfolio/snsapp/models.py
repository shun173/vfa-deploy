from django.db import models
from django.contrib.auth import get_user_model
from ecapp.models import Product


class Article(models.Model):
    """投稿記事"""
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    content = models.TextField(max_length=300)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, blank=True, null=True)
    evaluation = models.PositiveIntegerField(blank=True, null=True)
    good_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Good(models.Model):
    """いいねカウント"""
    pusher = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
