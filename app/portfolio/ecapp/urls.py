from django.urls import path
from . import views


app_name = 'ecapp'
urlpatterns = [
    path('', views.index, name='index'),
    path('fav_products/', views.fav_products, name='fav_products'),
    path('my_products/', views.my_products, name='my_products'),
    path('product/<int:product_id>/', views.detail, name='detail'),
    path('product/', views.detail_from_article, name='detail_from_article'),
    path('wheather_fav_new/', views.WheatherFavNew.as_view(),
         name='wheather_fav_new'),
    path('toggle_fav/', views.ToggleFav.as_view(), name='toggle_fav'),
    path('cart/<int:which_cart>/', views.cart, name='cart'),
    path('change_item_amount/<int:which_cart>/', views.change_item_amount,
         name='change_item_amount'),
    path('delete_cart_product/<int:which_cart>/<int:product_id>/',
         views.delete_cart_product, name='delete_cart_product'),
    path('order_history/', views.order_history, name='order_history'),
    path('sell/', views.sell, name='sell'),
    path('delete/<int:product_id>', views.delete, name='delete'),
]
