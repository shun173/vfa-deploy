import random

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.timezone import localtime
from faker import Faker
from rest_framework import status
from rest_framework.test import force_authenticate, APIClient, APITestCase

from ..models import Product
from ..views import ProductViewSet
from .factories import ProductFactory, UserFactory


class ProductApiTest(APITestCase):
    def test_post(self):
        fake = Faker()
        user = UserFactory()
        filename = 'default_icon.jpg'
        file = File(open('static/default_icon.jpg', 'rb'))
        uploaded_file = SimpleUploadedFile(
            filename, file.read(), content_type='multipart/form-data')
        client = APIClient()
        client.force_authenticate(user=user)
        data = {
            'name': fake.word(),
            'description': fake.text(),
            'price': random.randint(1, 10000),
            'amount': random.randint(1, 100),
            'image': uploaded_file,
            'owner': user.id
        }
        url = reverse('product-list')
        response = client.post(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)

        product = Product.objects.filter(name=data['name'])[0]
        self.assertEqual(product.name, data['name'])
        self.assertEqual(product.description, data['description'])
        self.assertEqual(product.price, data['price'])
        self.assertEqual(product.amount, data['amount'])
        self.assertIn('default_icon', product.image.url)
        self.assertEqual(product.owner, user)

    def test_get(self):
        user = UserFactory()
        product = ProductFactory()
        url = reverse('product-detail', kwargs={'pk': product.id})
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(url)
        created_at = response.data['created_at'].replace('T', ' ')
        response.data['created_at'] = created_at

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'amount': product.amount,
            'image': 'http://testserver' + product.image.url,
            'owner': product.owner.id,
            'created_at': str(localtime(product.created_at))
        })
