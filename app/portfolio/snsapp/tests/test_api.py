import random

from django.urls import reverse
from django.utils.timezone import localtime
from faker import Faker
from rest_framework import status
from rest_framework.test import force_authenticate, APIClient, APITestCase

from ..models import Article
from ..views import ArticleViewSet
from .factories import ArticleFactory, UserFactory
from ecapp.tests.factories import ProductFactory


class ArticleApiTest(APITestCase):
    def test_post(self):
        fake = Faker()
        user = UserFactory()
        product = ProductFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        data = {
            'author': user.id,
            'product': product.id,
            'evaluation': random.randint(1, 5),
            'content': fake.text()
        }
        url = reverse('article-list')
        response = client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.objects.count(), 1)

        article = Article.objects.filter(author=user)[0]
        self.assertEqual(article.author.id, data['author'])
        self.assertEqual(article.product.id, data['product'])
        self.assertEqual(article.evaluation, data['evaluation'])
        self.assertEqual(article.content, data['content'])
        self.assertEqual(article.good_count, 0)

    def test_get(self):
        user = UserFactory()
        article = ArticleFactory()
        url = reverse('article-detail', kwargs={'pk': article.id})
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(url)
        created_at = response.data['created_at'].replace('T', ' ')
        response.data['created_at'] = created_at

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'id': article.id,
            'author': article.author.id,
            'content': article.content,
            'product': article.product.id,
            'evaluation': article.evaluation,
            'good_count': 0,
            'created_at': str(localtime(article.created_at))
        })
