from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(*roles):
    """角色权限装饰器。

    用法::

        @role_required('teacher')
        def view(...): ...

        @role_required('teacher', 'admin')
        def view(...): ...
    """
    # 兼容旧写法：role_required(['teacher', 'admin'])
    if len(roles) == 1 and isinstance(roles[0], (list, tuple, set)):
        roles = tuple(roles[0])

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('users:login')
            profile = getattr(request.user, 'profile', None)
            role = getattr(profile, 'role', None)
            if role not in roles:
                messages.error(request, '您没有权限访问该页面！')
                return redirect('exams:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def teacher_required(view_func):
    """仅教师可访问。"""
    return role_required('teacher')(view_func)


def student_required(view_func):
    """仅学生可访问。"""
    return role_required('student')(view_func)


def admin_required(view_func):
    """仅管理员可访问。"""
    return role_required('admin')(view_func)