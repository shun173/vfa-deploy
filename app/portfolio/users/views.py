import json
import requests
import datetime
from django.conf import settings
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from .models import Friend, PointFluctuation, Questionnaire
from snsapp.models import Article
from ecapp.models import Product
from .forms import CustomUserCreationForm, MyPasswordChangeForm, MyPasswordResetForm, MySetPasswordForm, QuestionnaireForm, ProfileForm


def index(request):
    '''トップページを表示'''
    products = Product.objects.all().order_by('-id')
    products = products[:20]
    articles = Article.objects.all().order_by('-created_at')
    article_num = request.GET.get('articles')
    if not article_num:
        article_num = 0
    article_num = int(article_num)
    if article_num == len(articles) and article_num != 0:
        messages.warning(request, '既に全ての記事を表示しています')
    else:
        article_num += 10
        articles = articles[:article_num]
        article_num = len(articles)
    context = {
        'products': products,
        'articles': articles,
        'article_num': article_num,
        'next': 'top',
    }
    return render(request, 'users/index.html', context)


@login_required
def my_page(request):
    '''マイページを表示'''
    return render(request, 'users/my_page.html')


@login_required
def edit_profile(request):
    '''get:プロフィール編集ページを表示　post:プロフィール編集処理'''
    user = request.user
    # プロフィールが更新されたとき
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, request.FILES)
        if profile_form.is_valid():
            user.name = profile_form.cleaned_data['name']
            user.email = profile_form.cleaned_data['email']
            user.message = profile_form.cleaned_data['message']
            user.icon = profile_form.cleaned_data['icon']
            # 住所検索されたとき
            if 'search_address' in request.POST:
                zip_code = request.POST['zip_code']
                address = get_address(zip_code)
                profile_form = ProfileForm(
                    initial={'name': user.name, 'email': user.email, 'zip_code': zip_code, 'address': address})
                if not address:
                    messages.warning(request, "住所を取得できませんでした")
                    return redirect('users:edit_profile')
                return render(request, 'users/edit_profile.html', {'profile_form': profile_form})
            user.address = profile_form.cleaned_data['address']
            user.save()
            return redirect('users:my_page')
        else:
            messages.warning(request, '必須項目が入力されていません')
            return render(request, 'users/edit_profile.html', {'profile_form': profile_form})
    profile_form = ProfileForm(
        initial={'name': user.name, 'email': user.email, 'address': user.address, 'message': user.message, 'icon': user.icon})
    return render(request, 'users/edit_profile.html', {'profile_form': profile_form})


def user_detail(request, user_id):
    '''ユーザー詳細ページを表示'''
    user_model = get_user_model()
    user = user_model.objects.get(id=user_id)
    products = Product.objects.filter(owner=user).order_by('-created_at')
    articles = Article.objects.filter(author=user).order_by('-created_at')
    article_num = request.GET.get('articles')
    if not article_num:
        article_num = 0
    article_num = int(article_num)
    if article_num == len(articles) and article_num != 0:
        messages.warning(request, '既に全ての記事を表示しています')
    else:
        article_num += 10
        articles = articles[:article_num]
        article_num = len(articles)
    if Friend.objects.filter(owner=request.user).filter(friends=user):
        is_friend = True
    else:
        is_friend = False
    context = {
        'user': user,
        'products': products,
        'articles': articles,
        'is_friend': is_friend,
        'article_num': article_num,
        'next': 'user',
    }
    return render(request, 'users/user_detail.html', context)


@login_required
def friend_list(request):
    '''フレンドリストを表示'''
    user = request.user
    friend_instances = Friend.objects.filter(
        owner=user).order_by('-created_at')
    friends = []
    for friend_instance in friend_instances:
        friend = friend_instance.friends
        friends.append(friend)
    num = request.GET.get('page')
    friends = Paginator(friends, 10)
    friends = friends.get_page(num)
    return render(request, 'users/friend_list.html', {'friends': friends})


@login_required
def add_friend(request, user_id):
    '''ユーザーの友達状態を切り替える'''
    user = request.user
    user_model = get_user_model()
    friend = user_model.objects.get(id=user_id)
    friend_object = Friend.objects.filter(owner=user).filter(friends=friend)
    if friend_object:
        friend_object.delete()
    else:
        Friend.objects.create(owner=user, friends=friend)
    return redirect('users:user_detail', user_id=user_id)


@login_required
def point_history(request):
    '''ポイント履歴を表示'''
    user = request.user
    point_fluctuations = PointFluctuation.objects.filter(
        user=user).order_by('-created_at')
    num = request.GET.get('page')
    point_fluctuations = Paginator(point_fluctuations, 10)
    point_fluctuations = point_fluctuations.get_page(num)
    return render(request, 'users/point_history.html', {'point_fluctuations': point_fluctuations})


@login_required
def questionnaire(request):
    '''get:アンケートページを表示　post:アンケート回答処理'''
    user = request.user
    # アンケート回答済みのユーザーはリダイレクト
    questionnaire = Questionnaire.objects.filter(user=user)
    if questionnaire:
        messages.warning(request, 'アンケートに回答済みです')
        return redirect('users:my_page')

    questionnaire_form = QuestionnaireForm(request.POST or None)
    if questionnaire_form.is_valid():
        content = questionnaire_form.cleaned_data['content']
        evaluation = questionnaire_form.cleaned_data['evaluation']
        # ポイント付与
        user.point += 300
        user.save()
        PointFluctuation.objects.create(
            user=user, event='アンケートに回答', change=300)

        questionnaire = Questionnaire(
            user=user, content=content, evaluation=evaluation)
        questionnaire.save()
        # 開発者にメール送信
        subject = 'アンケート結果'
        message = f'評価　：　{evaluation}\n\n{content}'
        developer = get_user_model().objects.get(id=1)
        from_email = settings.DEFAULT_FROM_EMAIL
        developer.email_user(
            subject=subject, message=message, from_email=from_email)
        messages.success(request, 'アンケートにご協力いただきありがとうございます。300ポイントが付与されました。')
        return redirect('users:index')
    else:
        messages.warning(request, '必須項目が入力されていません')
    return render(request, 'users/questionnaire.html', {'questionnaire_form': questionnaire_form})


def signup(request):
    '''get:新規登録ページを表示　post:新規登録処理'''
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            input_email = form.cleaned_data['email']
            input_password = form.cleaned_data['password1']
            new_user = authenticate(
                email=input_email, password=input_password)
            if new_user is not None:
                login(request, new_user)
                return redirect('users:index')
        else:
            messages.warning(request, '無効な値が入力されました')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/signup.html', {'form': form})


class PasswordChange(PasswordChangeView):
    """パスワード変更ビュー"""
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('users:password_change_done')
    template_name = 'users/password_change.html'


class PasswordChangeDone(PasswordChangeDoneView):
    """パスワード変更後"""

    def get(self, request):
        messages.success(request, 'パスワードを変更しました')
        return render(request, 'users/login.html')


class PasswordReset(PasswordResetView):
    """パスワード変更用URLの送付ページ"""
    subject_template_name = 'users/mail_template/password_reset/subject.txt'
    email_template_name = 'users/mail_template/password_reset/message.txt'
    template_name = 'users/password_reset_form.html'
    form_class = MyPasswordResetForm
    success_url = reverse_lazy('users:password_reset_done')


class PasswordResetDone(PasswordResetDoneView):
    """パスワード変更用URLを送りましたページ"""
    template_name = 'users/password_reset_done.html'


class PasswordResetConfirm(PasswordResetConfirmView):
    """新パスワード入力ページ"""
    form_class = MySetPasswordForm
    success_url = reverse_lazy('users:password_reset_complete')
    template_name = 'users/password_reset_confirm.html'


class PasswordResetComplete(PasswordResetCompleteView):
    """新パスワード設定しましたページ"""

    def get(self, request):
        messages.success(request, 'パスワードを再設定しました')
        return render(request, 'users/login.html')


def get_address(zip_code):
    '''郵便番号から住所を取得'''
    REQUEST_URL = f'http://zipcloud.ibsnet.co.jp/api/search?zipcode={zip_code}'
    address = ''
    response = requests.get(REQUEST_URL, timeout=5)
    response = json.loads(response.text)
    result, api_status = response['results'], response['status']
    if api_status == 200 and result != None:
        result = result[0]
        address = result['address1'] + result['address2'] + result['address3']
    return address


@receiver(user_logged_in)
def user_loged_in_callback(sender, request, user, **kwargs):
    """連続ログインボーナス処理（ログインした際に呼ばれる）"""
    today = datetime.date.today()
    last_login_date = user.last_login_date
    if today == last_login_date:
        pass
    else:
        if not last_login_date:
            user.continuous_login = 1
            message = '初めまして'
        else:
            next_day = last_login_date + datetime.timedelta(days=1)
            if today == next_day:
                user.continuous_login += 1
            else:
                user.continuous_login = 1
            message = 'お帰りなさい'
        add_point = 100 * user.continuous_login
        messages.success(
            request, f'{user.name}さん、{message}。{user.continuous_login}日連続ログインボーナス：{add_point}ポイント 贈呈')
        user.point += add_point
        user.save()
        PointFluctuation.objects.create(
            user=user, event='連続ログインボーナス', change=add_point)
        user.last_login_date = today
        user.save()
