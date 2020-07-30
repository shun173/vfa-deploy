from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import EmailAuthenticationForm

app_name = 'users'
urlpatterns = [
    path('', views.index, name='index'),
    path('my_page/', views.my_page, name='my_page'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('user_detail/<int:user_id>/', views.user_detail, name='user_detail'),
    path('friend_list/', views.friend_list, name='friend_list'),
    path('add_friend/<int:user_id>', views.add_friend, name='add_friend'),
    path('point_history/', views.point_history, name='point_history'),
    path('questionnaire/', views.questionnaire, name='questionnaire'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_change/done', views.PasswordChangeDone.as_view(),
         name='password_change_done'),
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDone.as_view(),
         name='password_reset_done'),
    path('password_reset/confirm/<uidb64>/<token>/',
         views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('password_reset/complete/', views.PasswordResetComplete.as_view(),
         name='password_reset_complete'),
]
