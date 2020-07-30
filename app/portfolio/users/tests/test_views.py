import random
import re
import datetime

from faker import Faker
from django.urls import reverse
from django.test import Client
from django_webtest import WebTest
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session

from .factories import UserFactory
from ..models import Friend


class UserTest(WebTest):
    csrf_checks = False

    def test_signup(self):
        fake = Faker()
        url = reverse('users:signup')
        form = self.app.get(url).form
        email = fake.email()
        name = fake.name()
        password = fake.password()
        form['email'] = email
        form['name'] = name
        form['password1'] = password
        form['password2'] = password
        response = form.submit().follow()

        User = get_user_model()
        user = User.objects.all()[0]

        user = User.objects.get(name=name)
        self.assertIn(
            f'{name}さん、初めまして。1日連続ログインボーナス：100ポイント 贈呈', str(response))
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.email, email)
        self.assertEqual(user.point, 50100)

    # def test_signin(self):
        # password = Faker().password()
        # email = 'juntail@gmail.com'
        # password = 'ryohusoni1'
        # yesterday = datetime.date.today() - datetime.timedelta(days=1)
        # continuous_login = random.randint(1, 10)
        # user = UserFactory(email=email,
        #                    password=password,
        #                    last_login_date=yesterday,
        #                    continuous_login=continuous_login)

        # User = get_user_model()
        # user = User.objects.create(
        #     name='name', email='a@g.com', password='password')

        # print(user.is_authenticated)
        # s = Session.objects.all()
        # print(s)
        # for i in s:
        #     print(i)
        #     print(i.getdecode().get('_auth_user_id'))
        #     i.delete()
        # print(user.is_authenticated)
        # print(user)
        # print(user.session)

        # url = reverse('users:index')
        # response = self.app.get(url, user=user)
        # response.click(verbose=True)
        # response.click('ログアウト')
        # print(response)
        # logout_url = reverse('users:logout')
        # response = self.app.get(logout_url).follow()

        # user.is_authenticated = False
        # print(user.is_authenticated)
        # print(response)

        # url = reverse('users:login')
        # top_url = reverse('users:index')

        # response = self.app.get(top_url, extra_environ=dict(
        #     REMOTE_USER='juntail@gmail.com'))
        # print(response)
        # print(user.is_authenticated)

        # c = Client()
        # response = c.post(
        #     url, {'username': 'juntail@gmail.com', 'password': 'ryohusoni1'})
        # login = c.login(username='juntail@gmail.com', password='ryohusoni1')
        # print(login)
        # print(response.content.decode())
        # print(user.email)
        # print(user.password)

        # print(password)
        # print(user.password)
        # print(user.is_authenticated)

        # form['email'] = user.email
        # form['password'] = user.password
        # response = form.submit()
        # print(response)

        # continuous_login = continuous_login + 1
        # add_point = 100 * continuous_login

        # self.assertEqual(get_user_model().objects.count(), 1)
        # self.assertIn(
        # f'{user.name}さん、お帰りなさい。{continuous_login}日連続ログインボーナス：{add_point}ポイント 贈呈', str(response))
        # self.assertEqual(user.point, 50100)


class FriendTest(WebTest):
    csrf_checks = False

    def test_add_frien(self):
        user = UserFactory()
        friend = UserFactory()
        url = reverse('users:user_detail', kwargs={'user_id': friend.id})
        form = self.app.get(url, user=user).form
        response = form.submit('add_friend').follow()

        friend_model = Friend.objects.all()[0]
        self.assertIn('value="友達追加済み"', response)
        self.assertEqual(friend_model.owner, user)
        self.assertEqual(friend_model.friends, friend)
