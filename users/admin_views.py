"""管理员专用页面：风格与前台一致的用户 / 班级 / 课程 / 试卷管理。

和 Django admin 并存：Django admin 作为底层兜底，本模块提供朱红风格的运营视图。
"""
import secrets
import string

from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from classes.models import ClassMember, ClassRoom, Course
from exams.models import ExamPaper, ExamRecord, Question
from notifications.models import Notification

from .decorators import admin_required
from .models import UserProfile


def _random_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ======================================================================
# 用户管理
# ======================================================================
@admin_required
def manage_users(request):
    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    users = User.objects.select_related('profile').order_by('-date_joined')
    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) |
            Q(email__icontains=q) | Q(profile__student_id__icontains=q)
        )
    if role in ('admin', 'teacher', 'student'):
        users = users.filter(profile__role=role)

    counts = {
        'all': User.objects.count(),
        'admin': UserProfile.objects.filter(role='admin').count(),
        'teacher': UserProfile.objects.filter(role='teacher').count(),
        'student': UserProfile.objects.filter(role='student').count(),
    }
    return render(request, 'admin_panel/users.html', {
        'users': users[:300], 'q': q, 'role': role, 'counts': counts,
    })


@admin_required
@require_http_methods(['POST'])
def toggle_user_active(request, user_id):
    u = get_object_or_404(User, id=user_id)
    if u == request.user:
        messages.error(request, '不能禁用当前登录的自己')
    else:
        u.is_active = not u.is_active
        u.save(update_fields=['is_active'])
        messages.success(request, f'已{"启用" if u.is_active else "禁用"}用户 {u.username}')
    return redirect('users:manage_users')


@admin_required
@require_http_methods(['POST'])
def change_user_role(request, user_id):
    u = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('role')
    if u.profile.role == 'admin':
        messages.error(request, '管理员角色不可在此修改')
    elif new_role not in ('student', 'teacher'):
        messages.error(request, '只能切换为学生或教师')
    else:
        u.profile.role = new_role
        u.profile.save()
        messages.success(request,
                         f'已把 {u.username} 设为「{u.profile.get_role_display()}」')
    return redirect('users:manage_users')


@admin_required
def create_user(request):
    """管理员直接开账号，自动设置角色并填入学号/工号。"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip() or _random_password()
        first_name = request.POST.get('first_name', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'student')
        sid = request.POST.get('student_id', '').strip()

        if not username:
            messages.error(request, '用户名不能为空')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'用户名「{username}」已存在')
        elif role not in ('student', 'teacher'):
            # 管理员账号不允许通过此页面创建（请用 createsuperuser 或 seed_demo）
            messages.error(request, '只能创建学生或教师账号,管理员账号需由系统级命令创建')
        else:
            try:
                u = User.objects.create_user(
                    username=username, password=password,
                    first_name=first_name, email=email,
                )
                u.profile.role = role
                u.profile.student_id = sid
                u.profile.save()
                messages.success(
                    request,
                    f'账号 {username} 创建成功！初始密码:{password}(请告知用户)'
                )
                return redirect('users:manage_users')
            except IntegrityError as e:
                messages.error(request, f'创建失败:{e}')

    return render(request, 'admin_panel/user_form.html', {
        'mode': 'create', 'form_user': None,
    })


@admin_required
def edit_user(request, user_id):
    u = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        u.first_name = request.POST.get('first_name', '').strip()
        u.email = request.POST.get('email', '').strip()
        role = request.POST.get('role')
        sid = request.POST.get('student_id', '').strip()
        # 保护管理员账号:无法被降级为学生/教师
        if u.profile.role == 'admin':
            pass  # 管理员角色保持不变
        elif role in ('student', 'teacher'):
            u.profile.role = role
        u.profile.student_id = sid
        u.save()
        u.profile.save()
        messages.success(request, f'用户 {u.username} 已更新')
        return redirect('users:manage_users')

    return render(request, 'admin_panel/user_form.html', {
        'mode': 'edit', 'form_user': u,
    })


@admin_required
@require_http_methods(['POST'])
def reset_user_password(request, user_id):
    u = get_object_or_404(User, id=user_id)
    new_pwd = _random_password()
    u.set_password(new_pwd)
    u.save(update_fields=['password'])
    messages.success(
        request,
        f'已重置 {u.username} 的密码为:{new_pwd}(仅此一次显示,请妥善通知用户)',
    )
    return redirect('users:manage_users')


# ======================================================================
# 班级管理
# ======================================================================
@admin_required
def manage_classes(request):
    q = request.GET.get('q', '').strip()
    classes = ClassRoom.objects.select_related('head_teacher').annotate(
        student_num=Count('memberships', filter=Q(memberships__role='student'),
                          distinct=True),
        teacher_num=Count('memberships', filter=Q(memberships__role='teacher'),
                          distinct=True),
    ).order_by('-created_at')
    if q:
        classes = classes.filter(
            Q(name__icontains=q) | Q(grade__icontains=q) |
            Q(head_teacher__username__icontains=q) | Q(invite_code__iexact=q)
        )
    return render(request, 'admin_panel/classes.html', {
        'classes': classes, 'q': q,
        'total': ClassRoom.objects.count(),
    })


@admin_required
@require_http_methods(['POST'])
def delete_class(request, class_id):
    cls = get_object_or_404(ClassRoom, id=class_id)
    name = cls.name
    cls.delete()
    messages.success(request, f'班级「{name}」已删除')
    return redirect('users:manage_classes')


# ======================================================================
# 课程管理
# ======================================================================
@admin_required
def manage_courses(request):
    q = request.GET.get('q', '').strip()
    courses = Course.objects.select_related('classroom', 'teacher').order_by('-id')
    if q:
        courses = courses.filter(
            Q(name__icontains=q) | Q(teacher__username__icontains=q) |
            Q(classroom__name__icontains=q)
        )
    return render(request, 'admin_panel/courses.html', {
        'courses': courses, 'q': q, 'total': Course.objects.count(),
    })


@admin_required
@require_http_methods(['POST'])
def delete_course(request, course_id):
    c = get_object_or_404(Course, id=course_id)
    name = c.name
    c.delete()
    messages.success(request, f'课程「{name}」已删除')
    return redirect('users:manage_courses')


# ======================================================================
# 试卷审核
# ======================================================================
@admin_required
def manage_papers(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    papers = ExamPaper.objects.select_related('created_by', 'course').annotate(
        submission_count=Count('exam_records', distinct=True),
    ).order_by('-created_at')
    if q:
        papers = papers.filter(
            Q(title__icontains=q) | Q(created_by__username__icontains=q)
        )
    if status == 'published':
        papers = papers.filter(is_published=True)
    elif status == 'draft':
        papers = papers.filter(is_published=False)
    return render(request, 'admin_panel/papers.html', {
        'papers': papers, 'q': q, 'status': status,
        'counts': {
            'all': ExamPaper.objects.count(),
            'published': ExamPaper.objects.filter(is_published=True).count(),
            'draft': ExamPaper.objects.filter(is_published=False).count(),
        },
    })


@admin_required
@require_http_methods(['POST'])
def toggle_paper_publish(request, paper_id):
    p = get_object_or_404(ExamPaper, id=paper_id)
    p.is_published = not p.is_published
    p.save(update_fields=['is_published'])
    messages.success(request,
                     f'已{"发布" if p.is_published else "撤回"}《{p.title}》')
    return redirect('users:manage_papers')


@admin_required
@require_http_methods(['POST'])
def delete_paper(request, paper_id):
    p = get_object_or_404(ExamPaper, id=paper_id)
    title = p.title
    p.delete()
    messages.success(request, f'试卷「{title}」已删除')
    return redirect('users:manage_papers')


# ======================================================================
# 系统通知 · 广播发送
# ======================================================================
@admin_required
def broadcast_notice(request):
    """管理员群发系统通知。

    接收对象(audience):
      - all       : 所有在线用户
      - students  : 所有学生
      - teachers  : 所有教师
      - class:<id>: 指定班级的全体成员(学生 + 任课教师)
    """
    recent = Notification.objects.filter(
        sender=request.user, type='generic',
    ).order_by('-created_at')[:10]

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        audience = request.POST.get('audience', 'all')
        link = request.POST.get('link', '').strip()

        if not title:
            messages.error(request, '标题不能为空')
        elif not content:
            messages.error(request, '内容不能为空')
        else:
            # 根据受众选出目标用户
            recipients = User.objects.filter(is_active=True)
            if audience == 'students':
                recipients = recipients.filter(profile__role='student')
            elif audience == 'teachers':
                recipients = recipients.filter(profile__role='teacher')
            elif audience.startswith('class:'):
                try:
                    cls_id = int(audience.split(':', 1)[1])
                    member_ids = ClassMember.objects.filter(
                        classroom_id=cls_id,
                    ).values_list('user_id', flat=True)
                    recipients = recipients.filter(id__in=list(member_ids))
                except (ValueError, IndexError):
                    messages.error(request, '指定班级无效')
                    return redirect('users:broadcast_notice')

            # 发送者(管理员)自己也收到一份,方便存档+确认送达
            recipients = list(recipients)
            Notification.objects.bulk_create([
                Notification(
                    recipient=u, sender=request.user,
                    type='generic', title=title, message=content, link=link,
                ) for u in recipients
            ])
            messages.success(
                request,
                f'📢 已向 {len(recipients)} 位用户发送通知:《{title}》(含自己)',
            )
            return redirect('users:broadcast_notice')

    classes = ClassRoom.objects.select_related('head_teacher').order_by('name')
    stats = {
        'all': User.objects.filter(is_active=True).exclude(id=request.user.id).count(),
        'students': UserProfile.objects.filter(role='student',
                                               user__is_active=True).count(),
        'teachers': UserProfile.objects.filter(role='teacher',
                                               user__is_active=True).count(),
    }
    return render(request, 'admin_panel/broadcast.html', {
        'classes': classes, 'stats': stats, 'recent': recent,
    })
