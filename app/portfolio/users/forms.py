from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django import forms
from .models import Questionnaire
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

UserModel = get_user_model()


class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(max_length=254,
                             widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label=_("Password"), strip=False,
                               widget=forms.PasswordInput)
    error_messages = {
        'invalid_login': "Eメールアドレス または パスワードに誤りがあります。",
        'inactive': _("This account is inactive."),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

        # Set the label for the "email" field.
        self.email_field = UserModel._meta.get_field("email")
        if self.fields['email'].label is None:
            self.fields['email'].label = capfirst(
                self.email_field.verbose_name)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email is not None and password:
            self.user_cache = authenticate(
                self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'email': self.email_field.verbose_name})
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'], code='inactive')

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'name')


class MyPasswordChangeForm(PasswordChangeForm):
    """パスワード変更フォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MyPasswordResetForm(PasswordResetForm):
    """パスワードを忘れたときのフォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MySetPasswordForm(SetPasswordForm):
    """パスワード再設定フォーム（パスワードを忘れたとき）"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ProfileForm(forms.Form):
    name = forms.CharField(
        label='ユーザー名',
        max_length=20,
    )
    email = forms.EmailField(
        label='Eメールアドレス',
        max_length=50
    )
    zip_code = forms.CharField(
        label='郵便番号',
        max_length=7,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '数字７桁（ハイフンなし）'})
    )
    address = forms.CharField(
        label='住所',
        max_length=100,
        required=False
    )
    message = forms.CharField(
        label='メッセージ',
        max_length=50,
        required=False
    )
    icon = forms.ImageField(
        label='アイコン',
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class QuestionnaireForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = ['evaluation', 'content']


DATA = [
    ('全体', '全体'),
    ('友人のみ', '友人のみ')
]


class SearchForm(forms.Form):
    select = forms.ChoiceField(
        choices=DATA,
    )
    keyword = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '検索ワード'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
