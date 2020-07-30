import random
import re

from django.urls import reverse
from faker import Faker
from django_webtest import WebTest

from ..models import Article
from users.models import PointFluctuation, Friend
from ecapp.models import Sale
from ecapp.tests.factories import ProductFactory
from .factories import ArticleFactory, UserFactory


class PostTest(WebTest):
    csrf_checks = False

    def test_post(self):
        user = UserFactory()
        product = ProductFactory()
        Sale.objects.create(product=product, user=user,
                            amount=1, price=product.price)
        fake = Faker()
        url = reverse('snsapp:post_article')
        form = self.app.get(url, user=user).form

        content = fake.text()
        evaluation = random.randint(1, 5)
        form['content'] = content
        form['product'] = product.id
        form['evaluation'] = evaluation
        response = form.submit().follow()
        article = Article.objects.filter(author=user)[0]

        self.assertEqual(Article.objects.count(), 1)
        self.assertEqual(article.content, content)
        self.assertEqual(article.product, product)
        self.assertEqual(article.evaluation, evaluation)
        self.assertEqual(article.good_count, 0)
        self.assertIn('記事を投稿しました', response)
        self.assertIn(article.content, response)


class SearchTest(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory()
        friend = UserFactory()
        Friend.objects.create(owner=self.user, friends=friend)
        self.article = ArticleFactory(author=friend)
        self.url = reverse('snsapp:index')

    def test_text_all(self):
        article_text = self.article.content[:10]
        form = self.app.get(self.url, user=self.user).form
        form['keyword'] = article_text
        response = form.submit()
        response = str(response)

        message = re.search(
            f'&quot;{article_text.rstrip()}&quot;の検索結果（全体）', response)
        search = re.search(f'value="{article_text}"', response)
        article = re.search(f'<p>{self.article.content}</p>', response)

        self.assertTrue(message)
        self.assertTrue(search)
        self.assertTrue(article)

    def test_product_friend(self):
        product_name = self.article.product.name
        form = self.app.get(self.url, user=self.user).form
        form['keyword'] = product_name
        form['select'] = '友人のみ'
        response = form.submit()
        response = str(response)

        product_link = rf'''<a class="media-headig h4"
                                href="/ecapp/product/\?product_id={self.article.product.id}&article_id={self.article.id}">
                                {product_name}
                            </a>'''
        response_join = ''.join(response.split())
        product_join = ''.join(product_link.split())
        message = re.search(
            f'&quot;{product_name}&quot;の検索結果（友人のみ）', response)
        search = re.search(f'value="{product_name}"', response)
        article = re.search(product_join, response_join)

        self.assertTrue(message)
        self.assertTrue(search)
        self.assertTrue(article)
