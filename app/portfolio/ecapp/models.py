from django.db import models


class Product(models.Model):
    """商品"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField(default=0)
    amount = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to='product')
    owner = models.ForeignKey('users.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Sale(models.Model):
    """売上情報"""
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    user = models.ForeignKey('users.User', on_delete=models.PROTECT)
    amount = models.PositiveIntegerField(default=0)
    price = models.PositiveIntegerField("商品単価")
    created_at = models.DateTimeField(auto_now_add=True)
