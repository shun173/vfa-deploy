from rest_framework import serializers
from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ('id', 'author', 'content', 'product', 'evaluation',
                  'good_count', 'created_at')
