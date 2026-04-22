"""管理员后台完整联动验证：新建/编辑用户、重置密码、禁用启用、切换发布等真实写库。"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OnlineExamSys.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client

from classes.models import ClassRoom, Course
from exams.models import ExamPaper
from users.models import UserProfile


def section(t):
    print(f'\n========== {t} ==========')


def login_admin():
    c = Client()
    c.force_login(User.objects.get(username='admin'))
    return c


def test_manage_pages_load():
    section('[1] 管理后台四个页面均 200')
    c = login_admin()
    for url in ['/users/manage/users/',
                '/users/manage/classes/',
                '/users/manage/courses/',
                '/users/manage/papers/']:
        r = c.get(url)
        assert r.status_code == 200, f'{url} -> {r.status_code}'
        print(f'  [OK] {url}')


def test_create_edit_user():
    section('[2] 创建新用户 → 编辑 → 重置密码 → 禁用 → 改角色')
    c = login_admin()
    # 清理上轮残留
    User.objects.filter(username='demo_test').delete()

    # 2.1 创建
    r = c.post('/users/manage/users/new/', {
        'username': 'demo_test', 'password': 'demo123456',
        'first_name': '测试账号', 'email': 'demo@test.com',
        'role': 'student', 'student_id': 'DEMO001',
    }, follow=False)
    print(f'  创建: HTTP {r.status_code}')
    u = User.objects.get(username='demo_test')
    print(f'  [OK] user.id={u.id}  role={u.profile.role}  sid={u.profile.student_id}')
    assert u.profile.role == 'student'
    assert u.profile.student_id == 'DEMO001'
    assert u.check_password('demo123456')

    # 2.2 编辑：改姓名 + 角色升级为教师
    r = c.post(f'/users/manage/users/{u.id}/edit/', {
        'first_name': '测试教师', 'email': 'teacher@demo.com',
        'role': 'teacher', 'student_id': 'T999',
    }, follow=False)
    u.refresh_from_db()
    u.profile.refresh_from_db()
    print(f'  编辑后: name={u.first_name}  role={u.profile.role}')
    assert u.first_name == '测试教师'
    assert u.profile.role == 'teacher'

    # 2.3 重置密码
    old_hash = u.password
    r = c.post(f'/users/manage/users/{u.id}/reset-pwd/')
    u.refresh_from_db()
    print(f'  重置密码 HTTP {r.status_code}，密码已变: {u.password != old_hash}')
    assert u.password != old_hash

    # 2.4 禁用
    r = c.post(f'/users/manage/users/{u.id}/toggle/')
    u.refresh_from_db()
    assert u.is_active is False
    print(f'  禁用: is_active={u.is_active}')
    # 启用
    c.post(f'/users/manage/users/{u.id}/toggle/')
    u.refresh_from_db()
    assert u.is_active is True
    print(f'  启用: is_active={u.is_active}')

    # 2.5 清理
    u.delete()
    print('  [OK] 测试账号已清理')


def test_search_filter():
    section('[3] 搜索 + 角色筛选')
    c = login_admin()
    r = c.get('/users/manage/users/?q=admin')
    assert r.status_code == 200
    assert b'admin' in r.content
    r = c.get('/users/manage/users/?role=teacher')
    assert r.status_code == 200
    print('  [OK] 搜索+筛选正常')


def test_paper_toggle_publish():
    section('[4] 试卷发布/撤回切换')
    c = login_admin()
    p = ExamPaper.objects.first()
    assert p, '没有试卷可测试'
    origin = p.is_published
    r = c.post(f'/users/manage/papers/{p.id}/publish/')
    p.refresh_from_db()
    print(f'  切换 1: {origin} -> {p.is_published}')
    assert p.is_published != origin
    # 切回
    c.post(f'/users/manage/papers/{p.id}/publish/')
    p.refresh_from_db()
    assert p.is_published == origin
    print('  [OK] 状态已还原')


def test_classes_search():
    section('[5] 班级页搜索与数据注解')
    c = login_admin()
    r = c.get('/users/manage/classes/')
    assert r.status_code == 200
    # 确保 student_num / teacher_num 被正确注入
    cls = ClassRoom.objects.first()
    assert cls
    r2 = c.get(f'/users/manage/classes/?q={cls.name}')
    assert cls.name.encode() in r2.content
    print(f'  [OK] 按名称 "{cls.name}" 搜到班级')


def test_courses_list():
    section('[6] 课程列表 + 搜索')
    c = login_admin()
    course = Course.objects.first()
    assert course
    r = c.get(f'/users/manage/courses/?q={course.name}')
    assert r.status_code == 200
    assert course.name.encode() in r.content
    print(f'  [OK] 搜到课程 "{course.name}"')


def test_non_admin_blocked():
    section('[7] 非管理员不能访问 manage 页')
    c = Client()
    c.force_login(User.objects.get(username='student1'))
    for url in ['/users/manage/users/', '/users/manage/users/new/',
                '/users/manage/classes/', '/users/manage/courses/']:
        r = c.get(url, follow=False)
        assert r.status_code == 302, f'{url} 学生访问应重定向,实得 {r.status_code}'
    print('  [OK] 学生访问 manage 页全部被重定向')


if __name__ == '__main__':
    test_manage_pages_load()
    test_create_edit_user()
    test_search_filter()
    test_paper_toggle_publish()
    test_classes_search()
    test_courses_list()
    test_non_admin_blocked()
    print('\n>>>>>>>>>> 管理员后台联动测试全部通过 <<<<<<<<<<')
