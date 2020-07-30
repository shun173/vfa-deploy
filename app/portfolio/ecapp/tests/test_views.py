import random

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from faker import Faker
from django_webtest import WebTest

from ..models import Product, Sale
from snsapp.models import Article
from users.models import PointFluctuation
from ..forms import SellForm
from .factories import ProductFactory, UserFactory


class SellTest(WebTest):
    csrf_checks = False

    def test_sellform(self):
        fake = Faker()
        with open('static/default_icon.jpg', 'rb') as f:
            uploaded_file = SimpleUploadedFile(
                f.name, f.read(), content_type='multipart/form-data')
        data = {
            'name': fake.word(),
            'description': fake.text(),
            'price': random.randint(1, 10000),
            'amount': random.randint(1, 100)
        }
        files = {'image': uploaded_file}
        sell_form = SellForm(data, files)
        self.assertTrue(sell_form.is_valid())

    def test_sell(self):
        user = UserFactory()
        fake = Faker()
        url = reverse('ecapp:sell')
        form = self.app.get(url, user=user).form
        name = fake.name()
        description = fake.text()
        price = random.randint(1, 10000)
        amount = random.randint(1, 100)
        form['name'] = name
        form['description'] = description
        form['price'] = price
        form['amount'] = amount
        with open('static/default_icon.jpg', 'rb') as f:
            form['image'] = (f.name, f.read())

        response = form.submit().follow()
        product = Product.objects.get(name=name)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(product.name, name)
        self.assertEqual(product.description, description)
        self.assertEqual(product.price, price)
        self.assertEqual(product.amount, amount)
        self.assertIn('default_icon', product.image.url)
        self.assertIn('商品を出品しました', response)
        self.assertIn(product.name, response)


class CartTest(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory()
        self.product = ProductFactory()
        self.url = reverse('ecapp:detail', kwargs={
            'product_id': self.product.id})

    def test_buynow(self):
        detail_page = self.app.get(self.url, user=self.user)
        num = random.randint(1, self.product.amount)
        form = detail_page.form
        form['num'] = num
        cart_page = form.submit('buy_now')
        total_price = self.product.price * num
        total_price = "{:,}".format(total_price)

        self.assertEqual(
            self.app.session.get('instant_cart'), {str(self.product.id): num})
        self.assertIn('カート外から購入', cart_page)
        self.assertIn(self.product.name, cart_page)
        self.assertIn(total_price, cart_page)

    def test_tocart(self):
        detail_page = self.app.get(self.url, user=self.user)
        num = random.randint(1, self.product.amount)
        form = detail_page.form
        form['num'] = num
        cart_page = form.submit('to_cart').follow()
        total_price = self.product.price * num
        total_price = "{:,}".format(total_price)

        self.assertEqual(
            self.app.session.get('cart'), {str(self.product.id): num})
        self.assertIn('カート', cart_page)
        self.assertIn(self.product.name, cart_page)
        self.assertIn(total_price, cart_page)

    def test_goon(self):
        detail_page = self.app.get(self.url, user=self.user)
        num = random.randint(1, self.product.amount)
        form = detail_page.form
        form['num'] = num
        ec_top_page = form.submit('go_on').follow()

        self.assertEqual(
            self.app.session.get('cart'), {str(self.product.id): num})
        self.assertIn('EC TOP', ec_top_page)

    def test_toproduct(self):
        recomend_product = ProductFactory()
        another_user = UserFactory()
        Sale.objects.create(product=self.product, user=another_user,
                            price=random.randint(1, 10000), amount=random.randint(1, 100))
        Sale.objects.create(product=recomend_product, user=another_user,
                            price=random.randint(1, 10000), amount=random.randint(1, 100))

        detail_page = self.app.get(self.url, user=self.user)
        num = random.randint(1, self.product.amount)
        form = detail_page.form
        form['num'] = num
        recomended_page = form.submit('product').follow()

        self.assertEqual(
            self.app.session.get('cart'), {str(self.product.id): num})
        self.assertIn(recomend_product.name, recomended_page)


class DetailFromArticleTest(WebTest):
    csrf_checks = False

    def test_detail_from_article(self):
        user = UserFactory()
        author = UserFactory()
        product = ProductFactory()
        Article.objects.create(author=author, content=Faker().text,
                               product=product, evaluation=3)
        article = Article.objects.filter(author=author)[0]

        top_page = self.app.get('/', user=user)
        detail_page = top_page.click(article.product.name, index=1)

        self.assertEqual(self.app.session.get('product_from_article'),
                         {str(product.id): str(article.id)})
        self.assertIn(product.name, detail_page)


class BuyTest(WebTest):
    csrf_checks = False

    def test_buy_from_article(self):
        user = UserFactory()
        author = UserFactory()
        product = ProductFactory()
        Article.objects.create(author=author, content=Faker().text,
                               product=product, evaluation=3)
        article = Article.objects.filter(author=author)[0]

        top_page = self.app.get('/', user=user)
        detail_page = top_page.click(article.product.name, index=1)
        num = random.randint(1, product.amount)
        form = detail_page.form
        form['num'] = num
        cart_page = form.submit('to_cart').follow()
        form = cart_page.forms[2]
        response = form.submit('buy_product').follow()

        total_price = product.price * num
        sale = Sale.objects.get(product=product)
        pf_buyer = PointFluctuation.objects.get(user=user)
        pf_seller = PointFluctuation.objects.get(user=product.owner)
        pf_author = PointFluctuation.objects.get(user=author)

        self.assertIn('商品の購入が完了しました！', response)
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(sale.product.name, product.name)
        self.assertEqual(sale.user, user)
        self.assertEqual(sale.amount, num)
        self.assertEqual(sale.price, product.price)
        self.assertEqual(PointFluctuation.objects.count(), 3)
        self.assertEqual(pf_buyer.event, f'{product.name}を{num}個購入')
        self.assertEqual(pf_buyer.change, -total_price)
        # self.assertEqual(user.point, 50000 - total_price)
        self.assertEqual(pf_seller.event, f'{product.name}が{num}個売れた')
        self.assertEqual(pf_seller.change, total_price)
        # self.assertEqual(product.owner.point, 50000+total_price)
        content = str(article.content)
        if len(content) > 20:
            content = content[:20] + '...'
        self.assertEqual(pf_author.event, f'記事："{content}" からの商品購入')
        self.assertEqual(pf_author.change, int(total_price / 100))
        # self.assertEqual(author.point, 50000+int(total_price / 100))


class MeanEvalTest(WebTest):
    csrf_checks = False

    def test_mean_eval(self):
        user = UserFactory()
        product = ProductFactory()
        Sale.objects.create(product=product, user=user,
                            amount=1, price=product.price)
        fake = Faker()
        eval_num = random.randint(1, 20)
        eval_data = []
        for _ in range(eval_num):
            eval = random.randint(1, 5)
            eval_data.append(eval)
            Article.objects.create(
                author=user, product=product, content=fake.text, evaluation=eval)
        url = reverse('ecapp:detail', kwargs={'product_id': product.id})
        detail_page = self.app.get(url, user=user)

        sum = 0
        for i in range(len(eval_data)):
            sum += eval_data[i]
        mean_eval = round(sum / eval_num)

        self.assertEqual(Article.objects.count(), eval_num)
        self.assertIn(f'data-eval="{mean_eval}"', detail_page)
