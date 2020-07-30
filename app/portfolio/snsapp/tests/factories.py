import factory.fuzzy
import random
import datetime

from django.contrib.auth import get_user_model

from ..models import Article
from ecapp.models import Product
from ecapp.tests.factories import ProductFactory


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        django_get_or_create = ('email',)

    email = factory.Faker('email')
    name = factory.Faker('name')
    point = 50000
    address = factory.Faker('address')
    icon = factory.Faker('image_url')
    message = factory.Faker('word')
    last_login_date = datetime.date.today()


class ArticleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Article

    author = factory.SubFactory(UserFactory)
    content = factory.Faker('text')
    product = factory.SubFactory(ProductFactory)
    evaluation = random.randint(1, 5)
