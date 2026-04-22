from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class UserRegisterForm(UserCreationForm):
    password1 = forms.CharField(
        label='密码', strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control',
                                           'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='确认密码', strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control',
                                           'autocomplete': 'new-password'}),
    )
    username = forms.CharField(
        label='用户名',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    real_name = forms.CharField(
        label='真实姓名', max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='邮箱（选填）', required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    role = forms.ChoiceField(
        choices=(('student', '学生'), ('teacher', '教师')),
        label='注册角色',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    student_id = forms.CharField(
        max_length=50, required=False, label='学号/工号',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['username', 'real_name', 'email',
                   'password1', 'password2', 'role', 'student_id']

    def save(self, commit=True):
        user = super().save(commit=False)
        real_name = self.cleaned_data.get('real_name') or ''
        # 真实姓名拆成 first/last name 存入 User
        user.first_name = real_name
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.student_id = self.cleaned_data['student_id']
            profile.save()
        return user


class LoginForm(forms.Form):
    """登录表单——关键：增加角色选择字段，登录时校验。"""
    ROLE_CHOICES = (
        ('student', '学生'),
        ('teacher', '教师'),
        ('admin', '管理员'),
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, label='我是',
        widget=forms.RadioSelect(attrs={'class': 'role-radio'}),
        initial='student',
    )
    username = forms.CharField(
        label='用户名',
        widget=forms.TextInput(attrs={'class': 'form-control',
                                       'placeholder': '请输入用户名'}),
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control',
                                           'placeholder': '请输入密码'}),
    )
