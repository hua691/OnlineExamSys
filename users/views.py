"""用户登录 / 注册 / 退出。

关键修改：
  - 登录表单增加"我是(学生/教师/管理员)"选项；登录时严格校验选择的角色与账号实际角色一致，杜绝越权。
  - 登录成功按角色跳转到各自 dashboard。
"""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import LoginForm, UserRegisterForm
from .models import UserProfile


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '注册成功，欢迎加入！')
            return redirect('exams:dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('exams:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if not user:
                messages.error(request, '用户名或密码错误')
            else:
                profile = getattr(user, 'profile', None)
                if profile is None:
                    # 没有档案则按"学生"新建；管理员登录用 is_superuser 兜底
                    profile = UserProfile.objects.create(
                        user=user,
                        role='admin' if user.is_superuser else 'student',
                    )
                # admin 登录也允许 superuser 通过
                actual_role = profile.role or ('admin' if user.is_superuser else 'student')
                if actual_role != role:
                    role_display = dict(LoginForm.ROLE_CHOICES).get(role, role)
                    messages.error(
                        request,
                        f'该账号不是「{role_display}」身份，无法以此身份登录',
                    )
                else:
                    login(request, user)
                    return redirect('exams:dashboard')
    else:
        form = LoginForm(initial={'role': request.GET.get('role', 'student')})

    return render(request, 'users/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.success(request, '已退出登录')
    return redirect('users:login')
