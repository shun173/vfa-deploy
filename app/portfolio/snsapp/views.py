import re
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework import permissions, authentication
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from .models import Article, Good
from .forms import ArticleForm
from users.models import Friend, PointFluctuation
from users.forms import SearchForm
from ecapp.models import Product
from .serializers import ArticleSerializer


def index(request):
    '''get:snsトップページを表示　post:検索結果で絞り込んでsnsトップページを表示'''
    search_form = SearchForm(request.POST or None)
    articles = Article.objects.all().order_by('-created_at')
    # 検索フォーム
    if request.method == 'POST':
        if search_form.is_valid():
            user = request.user
            select = search_form.cleaned_data['select']
            keyword = search_form.cleaned_data['keyword']

            # ユーザー選択時の処理
            if select == '友人のみ':
                result_users = []
                if user.is_authenticated:
                    for friend_instance in Friend.objects.filter(owner=user):
                        friend = friend_instance.friends
                        result_users.append(friend)
            if select == '全体':
                user_model = get_user_model()
                result_users = user_model.objects.all()

            searched_articles = []
            for result_user in result_users:
                articles = Article.objects.filter(author=result_user)
                for article in articles:
                    searched_articles.append(article)

            # ワード検索時の処理
            if keyword:
                articles = []
                for article in searched_articles:
                    author = article.author.name
                    content = article.content
                    product = article.product
                    if product:
                        product = product.name
                    else:
                        product = ''
                    text_list = [author, content, product]
                    text = ' '.join(text_list)
                    if re.findall(keyword, text, re.IGNORECASE):
                        articles.append(article)
                messages.success(request, f'"{keyword}"の検索結果（{select}）')
            if not keyword:
                articles = searched_articles
                messages.success(request, f'絞り込み（{select}）')
        else:
            messages.warning(request, '無効な検索です')
            return redirect('snsapp:index')

    num = request.GET.get('page')
    if not num:
        num = 1
    articles = Paginator(articles, 20)
    articles = articles.get_page(num)
    context = {
        'search_form': search_form,
        'articles': articles,
        'next': 'sns',
    }
    return render(request, 'snsapp/index.html', context)


@login_required
def good_articles(request):
    '''いいねした記事で絞り込んでsnsトップページを表示'''
    user = request.user
    good_objects = Good.objects.filter(pusher=user).order_by('-created_at')
    articles = []
    for good in good_objects:
        article = good.article
        articles.append(article)
    num = request.GET.get('page')
    articles = Paginator(articles, 20)
    articles = articles.get_page(num)
    return render(request, 'snsapp/index.html', {'articles': articles})


@login_required
def my_articles(request):
    '''自身の記事で絞り込んでsnsトップページを表示'''
    user = request.user
    articles = Article.objects.filter(author=user).order_by('-created_at')
    num = request.GET.get('page')
    articles = Paginator(articles, 20)
    articles = articles.get_page(num)
    return render(request, 'snsapp/index.html', {'articles': articles})


@login_required
def post_article(request):
    '''get:記事投稿ページを表示　post:記事投稿処理'''
    if request.method == 'POST':
        author = request.user
        content = request.POST['content']
        product_id = request.POST['product']
        if product_id:
            product = Product.objects.get(pk=product_id)
            evaluation = request.POST['evaluation']
            article = Article.objects.create(
                author=author, content=content, product=product, evaluation=evaluation)
        else:
            article = Article.objects.create(author=author, content=content)
        article.save()
        messages.success(request, '記事を投稿しました')
        return redirect('snsapp:index')
    else:
        user_id = request.user.id
        article_form = ArticleForm(user_id=user_id)
    return render(request, 'snsapp/post_article.html', {'article_form': article_form})


@login_required
@require_POST
def delete(request, article_id):
    '''自身の記事を削除し、元のページを表示'''
    article = Article.objects.get(id=article_id)
    article.delete()
    if 'top' in request.POST:
        return redirect('users:index')
    elif 'user' in request.POST:
        user_id = request.user.id
        return redirect('users:user_detail', user_id=user_id)
    elif 'product' in request.POST:
        product_id = request.POST.get('product_id')
        return redirect('ecapp:detail', product_id=product_id)
    elif 'sns' in request.POST:
        return redirect('snsapp:index')


class GoodedArticles(APIView):
    '''いいねした記事のIDを返す'''

    def get(self, request):
        article_ids = []
        if request.user.is_authenticated:
            good_instances = Good.objects.filter(pusher=request.user)
            for good_instance in good_instances:
                gooded_article = good_instance.article
                article_ids.append(gooded_article.id)
            # 削除されている投稿を取り除く
            for i, article_id in enumerate(article_ids):
                if not Article.objects.filter(id=article_id):
                    article_ids.pop(i)
        data = {
            'article_ids': article_ids,
        }
        return JsonResponse(data, safe=False)


class ChangeGood(APIView):
    '''記事のいいね状態を切り替える'''
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        pk = request.GET.get('pk')
        article = get_object_or_404(Article, pk=pk)
        good = Good.objects.filter(pusher=user).filter(article=article)
        # 既にgoodを押していた場合
        if good:
            article.good_count -= 1
            article.save()
            PointFluctuation.objects.create(
                user=article.author, event=f'記事"{article.content}"のgoodが外されました', change=-1
            )
            good.delete()
        # 新しくgoodを押した場合
        else:
            article.good_count += 1
            article.save()
            PointFluctuation.objects.create(
                user=article.author, event=f'記事"{article.content}"にgoodが押されました', change=1
            )
            Good.objects.create(
                pusher=user, article=article
            )
        return Response(None)


class ArticleViewSet(viewsets.ModelViewSet):
    """API endpoint"""
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated]
