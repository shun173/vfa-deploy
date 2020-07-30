import factory.fuzzy
import random
import datetime

from django.contrib.auth import get_user_model

from ..models import Product


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


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('word')
    description = factory.Faker('text')
    price = random.randint(1, 100)
    amount = random.randint(1, 100)
    image = factory.Faker('image_url')
    owner = factory.SubFactory(UserFactory)
    created_at = str(factory.Faker('date_time'))
