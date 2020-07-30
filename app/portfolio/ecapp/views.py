import re
import requests
import datetime
import collections

from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework import permissions, authentication
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Friend, PointFluctuation
from users.forms import SearchForm, ProfileForm
from users.views import get_address
from snsapp.models import Article
from .models import Product, Sale
from .forms import AddToCartForm, SellForm
from .serializers import ProductSerializer


def index(request):
    '''get:ecトップページを表示　post:検索結果で絞り込んでecトップページを表示'''
    search_form = SearchForm(request.POST or None)
    products = Product.objects.all().order_by('-created_at')
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

            searched_products = []
            for result_user in result_users:
                products = Product.objects.filter(owner=result_user)
                for product in products:
                    searched_products.append(product)

            # ワード検索時の処理
            if keyword:
                products = []
                for product in searched_products:
                    name = product.name
                    owner = product.owner.name
                    description = product.description
                    if not description:
                        description = ''
                    text_list = [name, owner, description]
                    text = ' '.join(text_list)
                    if re.findall(keyword, text, re.IGNORECASE):
                        products.append(product)
                messages.success(request, f'"{keyword}"の検索結果（{select}）')
            if not keyword:
                products = searched_products
                messages.success(request, f'絞り込み（{select}）')
        else:
            messages.warning(request, '無効な検索です')
            return redirect('ecapp:index')

    num = request.GET.get('page')
    if not num:
        num = 1
    products = Paginator(products, 12)
    products = products.get_page(num)
    context = {
        'search_form': search_form,
        'products': products
    }
    return render(request, 'ecapp/index.html', context)


@login_required
def fav_products(request):
    '''お気に入り商品を絞り込んでecトップページを表示'''
    user = request.user
    products = user.fav_products.all().order_by('-created_at')
    num = request.GET.get('page')
    if not num:
        num = 1
    products = Paginator(products, 12)
    products = products.get_page(num)
    return render(request, 'ecapp/index.html', {'products': products})


@login_required
def my_products(request):
    '''自身の商品を絞り込んでecトップページを表示'''
    user = request.user
    products = Product.objects.filter(owner=user).order_by('-created_at')
    num = request.GET.get('page')
    if not num:
        num = 1
    products = Paginator(products, 12)
    products = products.get_page(num)
    return render(request, 'ecapp/index.html', {'products': products})


def detail(request, product_id):
    '''get:商品詳細ページを表示　post:商品をカートに入れ、カートページを表示
    {product_id:商品ID}'''
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        num = request.POST['num']
        num = int(num)
        if num == 0:
            messages.warning(request, '個数を選択してください')
            return redirect('ecapp:detail', product_id=product_id)
        # 今すぐ購入が押されたとき
        if 'buy_now' in request.POST:
            cart_products = {product: num}
            purchase_form = ProfileForm(request.POST, None)
            total_price = product.price * num
            request.session['instant_cart'] = {str(product_id): num}
            context = {
                'purchase_form': purchase_form,
                'cart_products': cart_products,
                'total_price': total_price,
                'which_cart': 1,
            }
            return render(request, 'ecapp/cart.html', context)
        # カートに入れるが押された時
        else:
            if 'cart' in request.session:
                if str(product_id) in request.session['cart']:
                    request.session['cart'][str(product_id)] += num
                else:
                    request.session['cart'][str(product_id)] = num
            else:
                request.session['cart'] = {str(product_id): num}
            messages.success(request, f"{product.name}を{num}個カートに入れました！")
            # カートへが押された時
            if 'to_cart' in request.POST:
                return redirect('ecapp:cart', which_cart=0)
            # 買い物を続けるが押された時
            elif 'go_on' in request.POST:
                return redirect('ecapp:index')
            # リコメンド商品が押された時
            elif 'product' in request.POST:
                next_product_id = request.POST['product']
                return redirect('ecapp:detail', product_id=next_product_id)
    else:
        # 商品の評価記事と平均評価、評価数を取り出す
        articles = product.article_set.all().order_by('-created_at')
        if articles:
            total = 0
            for article in articles:
                total += article.evaluation
            review_num = len(articles)
            mean = total / review_num
            mean_eval = round(mean)
        else:
            mean_eval = 0
            review_num = 0
        # 表示する記事数の処理
        # param {articles:現在表示している記事数}
        article_num = request.GET.get('articles')
        if not article_num:
            article_num = 0
        article_num = int(article_num)
        if article_num == len(articles) and article_num != 0:
            messages.warning(request, '既に全ての記事を表示しています')
        else:
            article_num += 10
            articles = articles[:article_num]
        # リコメンドする商品
        # 同商品を買ったユーザーが買った別商品（多い順に３つ、同数の時は購入日付が近いもの）
        rel_products = []
        self_sales = Sale.objects.filter(
            product=product).order_by('-created_at')
        for self_sale in self_sales:
            user = self_sale.user
            sales = Sale.objects.filter(user=user)
            for sale in sales:
                recommend_product = sale.product
                if recommend_product.id == product_id:
                    continue
                rel_products.append(recommend_product)
        recommend_products = []
        recommend_products_col = collections.Counter(
            rel_products).most_common(3)
        for recommend_product in recommend_products_col:
            recommend_products.append(recommend_product[0])

        add_to_cart_form = AddToCartForm(product_id=product_id)
        context = {
            'product': product,
            'articles': articles,
            'evaluation': mean_eval,
            'review_num': review_num,
            'article_num': article_num,
            'recommend_products': recommend_products,
            'add_to_cart_form': add_to_cart_form,
            'next': 'product',
        }
    return render(request, 'ecapp/detail.html', context)


def detail_from_article(request):
    '''商品の評価記事から商品詳細ページに飛んだ場合、セッションに商品IDと記事IDを記録'''
    product_id = request.GET.get('product_id')
    article_id = request.GET.get('article_id')
    if 'product_from_article' in request.session:
        request.session['product_from_article'][str(
            product_id)] = str(article_id)
    else:
        request.session['product_from_article'] = {
            str(product_id): str(article_id)}
    product_id = int(product_id)
    return detail(request, product_id)


class WheatherFavNew(APIView):
    '''お気に入り商品と一週間以内に出品された商品のIDを返す'''

    def get(self, request):
        fav_ids = []
        new_ids = []
        if request.user.is_authenticated:
            user = request.user
            fav_products = user.fav_products.all()
            for product in fav_products:
                fav_ids.append(product.id)

        for product in Product.objects.all():
            old = product.created_at + datetime.timedelta(days=7)
            if datetime.datetime.today().astimezone() < old:
                new_ids.append(product.id)

        data = {
            'fav_ids': fav_ids,
            'new_ids': new_ids,
        }
        return JsonResponse(data, safe=False)


class ToggleFav(APIView):
    '''商品のお気に入り状態を切り替える'''
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        pk = request.GET.get('pk')
        product = get_object_or_404(Product, pk=pk)
        # 既にgoodを押していた場合
        if product in user.fav_products.all():
            user.fav_products.remove(product)
        # 新しくgoodを押した場合
        else:
            user.fav_products.add(product)
        return Response(None)


@login_required
def cart(request, which_cart):
    '''get:カートページを表示　post:購入処理
    {which_cart:0→カートセッション、1→インスタントカートセッション}'''
    user = request.user
    if which_cart == 0:
        cart = request.session.get('cart', {})
    else:
        cart = request.session.get('instant_cart', {})
    cart_products = dict()
    total_price = 0
    for product_id, num in cart.items():
        product = Product.objects.get(id=product_id)
        cart_products[product] = num
        total_price += product.price * num

    purchase_form = ProfileForm(request.POST, None)
    if request.method == 'POST':
        # 住所検索ボタンが押された場合
        if 'search_address' in request.POST:
            zip_code = request.POST['zip_code']
            address = get_address(zip_code)
            if not address:
                messages.warning(request, '住所を取得できませんでした。')
                return redirect('ecapp:cart', which_cart=which_cart)
            purchase_form = ProfileForm(
                initial={'zip_code': zip_code, 'address': address})
        # 購入ボタンが押された場合
        if 'buy_product' in request.POST:
            if not bool(cart):
                messages.warning(request, "カートは空です。")
                return redirect('ecapp:cart', which_cart=which_cart)
            if total_price > user.point:
                messages.warning(request, "所持ポイントが足りません。")
                return redirect('ecapp:cart', which_cart=which_cart)
            for product_id in cart:
                product = Product.objects.get(pk=product_id)
                if product.owner == user:
                    messages.warning(request, "自身が出品した商品は購入できません。")
                    return redirect('ecapp:cart', which_cart=which_cart)
            if not user.address:
                address = request.POST['address']
                if not address:
                    messages.warning(request, "住所の入力は必須です。")
                    return redirect('ecapp:cart', which_cart=which_cart)
                user.address = address
                user.save()

            for product_id, num in cart.items():
                if not Product.objects.filter(pk=product_id).exists():
                    del cart[product_id]
                product = Product.objects.get(pk=product_id)
                product.amount -= num
                product.save()
                sale = Sale(product=product, user=user,
                            amount=num, price=product.price)
                sale.save()
                # ポイント履歴を記録
                # 購入者
                sum = product.price * num
                PointFluctuation.objects.create(
                    user=user, event=f'{product.name}を{num}個購入', change=-sum)
                # 出品者
                owner = product.owner
                owner.point += sum
                owner.save()
                PointFluctuation.objects.create(
                    user=owner, event=f'{product.name}が{num}個売れた', change=sum)
                # 出品者にメール送信
                subject = '商品が購入されました'
                message = f'''商品　：　{product.name}　が　{num}個　購入されました。\n\n
                            購入者　：　{user.name}\n
                            住所　：　{user.address}\n\n
                            上記の住所に商品を届けてください。その後{sum}ポイントが付与されます。
                '''
                from_email = settings.DEFAULT_FROM_EMAIL
                owner.email_user(
                    subject=subject, message=message, from_email=from_email)
                # 紹介記事のリンクから購入された商品の場合、紹介者にもポイント付与
                # request.session['product_from_article]=={str(product_id): str(article_id)}
                products = request.session.get('product_from_article')
                if products:
                    if product_id in products:
                        article_id = products[str(product_id)]
                        article = Article.objects.get(id=article_id)
                        author = article.author
                        author.point += int(sum / 100)
                        # 記事内容を短縮
                        content = str(article.content)
                        if len(content) > 20:
                            content = content[:20] + '...'
                        PointFluctuation.objects.create(
                            user=author, event=f'記事："{content}" からの商品購入', change=int(sum/100))
                        del request.session['product_from_article'][str(
                            product_id)]
            user.point -= total_price
            user.save()
            if which_cart == 0:
                del request.session['cart']
            else:
                del request.session['instant_cart']
            messages.success(request, "商品の購入が完了しました！")
            return redirect('ecapp:cart', which_cart=which_cart)
    # ページ処理
    num = request.GET.get('page')
    if not num:
        num = 1
    products = []
    for product in cart_products:
        products.append(product)
    products = Paginator(products, 5)
    products = products.get_page(num)
    context = {
        'purchase_form': purchase_form,
        'cart_products': cart_products,
        'total_price': total_price,
        'products': products,
        'which_cart': which_cart,
    }
    return render(request, 'ecapp/cart.html', context)


@login_required
@require_POST
def change_item_amount(request, which_cart):
    '''カートに入っている商品の個数を変更
    {which_cart:0→カートセッション、1→インスタントカートセッション}'''
    product_id = request.POST["product_id"]
    product_id = str(product_id)
    if which_cart == 0:
        cart_session = request.session['cart']
    else:
        cart_session = request.session['instant_cart']
    if product_id in cart_session:
        if 'action_remove' in request.POST:
            cart_session[product_id] -= 1
        if 'action_add' in request.POST:
            product = Product.objects.get(id=int(product_id))
            if cart_session[product_id] < product.amount:
                cart_session[product_id] += 1
            else:
                messages.warning(request, '在庫数をご確認ください。')
        if cart_session[product_id] <= 0:
            del cart_session[product_id]
    return redirect('ecapp:cart', which_cart=which_cart)


@login_required
@require_POST
def delete_cart_product(request, which_cart, product_id):
    '''カートに入っている商品をカートから削除
    {which_cart:0→カートセッション、1→インスタントカートセッション,
    product_id:商品ID}'''
    if which_cart == 0:
        cart_session = request.session['cart']
        product_id = str(product_id)
        if product_id in cart_session:
            del cart_session[product_id]
    else:
        del request.session['instant_cart']
    return redirect('ecapp:cart', which_cart=0)


@login_required
def order_history(request):
    '''購入履歴を表示'''
    user = request.user
    sales = Sale.objects.filter(user=user).order_by('-created_at')
    num = request.GET.get('page')
    sales = Paginator(sales, 5)
    sales = sales.get_page(num)
    return render(request, 'ecapp/order_history.html', {'sales': sales})


@login_required
def sell(request):
    '''get:出品ページを表示　post:出品処理'''
    if request.method == 'POST':
        sell_form = SellForm(request.POST, request.FILES)
        if sell_form.is_valid():
            product = sell_form.save(commit=False)
            product.owner = request.user
            product.save()
            messages.success(request, '商品を出品しました')
            return redirect('ecapp:my_products')
        else:
            messages.warning(request, '必須項目が入力されていません')
            return redirect('ecapp:sell')
    else:
        sell_form = SellForm()
    return render(request, 'ecapp/sell.html', {'sell_form': sell_form})


@login_required
@require_POST
def delete(request, product_id):
    '''自身の商品の出品を取り消す
    {product_id:商品ID}'''
    product = Product.objects.get(id=product_id)
    product.delete()
    return redirect('ecapp:my_products')


class ProductViewSet(viewsets.ModelViewSet):
    """API endpoint"""
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
