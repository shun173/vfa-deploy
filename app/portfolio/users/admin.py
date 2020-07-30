from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import ugettext_lazy as _
from .models import User, PointFluctuation, Questionnaire, Friend


class MyUserChangeForm(UserChangeForm):
    """User情報を変更するフォーム"""
    class Meta:
        model = User
        fields = '__all__'


class MyUserCreationForm(UserCreationForm):
    """Userを作成するフォーム"""
    class Meta:
        model = User
        fields = ('email', 'name')


class MyUserAdmin(UserAdmin):
    """カスタムユーザーモデルのAdmin"""
    fieldsets = (
        (None, {'fields': ('email',  'password', 'message', 'icon',
                           'fav_products', 'point', 'continuous_login')}),
        (_('Personal info'), {
         'fields': ('name', 'address')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {
         'fields': ('last_login', 'last_login_date', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    form = MyUserChangeForm
    add_form = MyUserCreationForm
    list_display = ('email', 'name', 'address', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'name')
    ordering = ('email',)


admin.site.register(User, MyUserAdmin)
admin.site.register(Friend)
admin.site.register(PointFluctuation)
admin.site.register(Questionnaire)
