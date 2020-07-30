from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth import get_user_model
from ecapp.models import Product


class UserManager(BaseUserManager):
    """カスタムユーザーマネージャー"""
    use_in_migrations = True

    def _create_user(self, email, name, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        if not name:
            raise ValueError('The given name must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_user(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, name, password, **extra_fields)

    def create_superuser(self, email, name, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """カスタムユーザーモデル"""
    initial_point = 50000
    email = models.EmailField("メールアドレス", unique=True)
    name = models.CharField("ユーザー名", max_length=50)
    address = models.CharField(max_length=100, blank=True, null=True)
    icon = models.ImageField(upload_to='icons', blank=True, null=True)
    message = models.TextField(max_length=50, blank=True, null=True)
    point = models.PositiveIntegerField(default=initial_point)
    fav_products = models.ManyToManyField(Product, blank=True)
    is_staff = models.BooleanField("is_staff", default=False)
    is_active = models.BooleanField("is_activ", default=True)
    date_joined = models.DateTimeField("date_joind", default=timezone.now)
    last_login = models.DateTimeField("last_login", blank=True, null=True)
    last_login_date = models.DateField(blank=True, null=True)
    continuous_login = models.PositiveIntegerField(default=0)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user. """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return self.email


class Friend(models.Model):
    """友達を記録"""
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='friend_owner')
    friends = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class PointFluctuation(models.Model):
    """各ユーザーのポイントの変化を記録する"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.CharField(max_length=100)
    change = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Questionnaire(models.Model):
    """アンケートモデル"""
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    evaluation = models.IntegerField(default=3)
    content = models.TextField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
