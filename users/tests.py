"""角色隔离与权限测试。

覆盖点：
  1. 未登录访问受保护 URL → 跳转登录
  2. 学生访问教师/管理员 URL → 被拒
  3. 教师访问学生专属 URL → 被拒
  4. 登录时角色选择错误 → 被拒
  5. 学生无法做其他班级的试卷
  6. 教师无法编辑别人创建的试题/试卷
  7. 非课程教师无法发布公告
  8. 讨论区仅课程成员可访问
"""
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from classes.models import (ClassMember, ClassRoom, Course,
                            CourseAnnouncement, DiscussionTopic)
from exams.models import ExamPaper, Question
from users.models import UserProfile


def _make_user(username, role, password='pass1234'):
    """创建指定角色的用户（post_save 信号会自动建 Profile，再更新 role）。"""
    u = User.objects.create_user(username=username, password=password,
                                 first_name=username)
    u.profile.role = role
    u.profile.save()
    return u


class RoleIsolationTests(TestCase):
    """三种角色访问各自受保护页面的权限隔离。"""

    @classmethod
    def setUpTestData(cls):
        cls.student = _make_user('alice', UserProfile.ROLE_STUDENT)
        cls.teacher = _make_user('bob', UserProfile.ROLE_TEACHER)
        cls.admin_user = _make_user('carol', UserProfile.ROLE_ADMIN)

    # ------------------------- 未登录 --------------------------
    def test_anonymous_redirected_to_login(self):
        c = Client()
        for url in ['/exams/', '/exams/questions/', '/exams/student/todo/',
                    '/classes/mine/']:
            resp = c.get(url, follow=False)
            self.assertIn(resp.status_code, (302, 301),
                          f'{url} 未登录应被重定向，实得 {resp.status_code}')
            self.assertIn('/users/login', resp.url,
                          f'{url} 应跳转到登录页，实得 {resp.url}')

    # ------------------------- 学生不能访问教师 URL --------------------------
    def test_student_forbidden_from_teacher_pages(self):
        c = Client()
        c.force_login(self.student)
        protected = [
            '/exams/questions/',
            '/exams/questions/create/',
            '/exams/papers/',
            '/exams/papers/create/',
            '/exams/teacher/correction/',
            '/classes/create/',           # 创建班级（仅教师）
            '/classes/course/create/',    # 创建课程（仅教师）
        ]
        for url in protected:
            resp = c.get(url, follow=False)
            # role_required 会 redirect 到 dashboard + 带 error message
            self.assertEqual(resp.status_code, 302,
                             f'{url} 学生访问应被装饰器挡下')

    # ------------------------- 教师不能访问学生专属 URL --------------------------
    def test_teacher_forbidden_from_student_only_pages(self):
        c = Client()
        c.force_login(self.teacher)
        protected = [
            '/exams/student/todo/',
            '/exams/student/papers/',
            '/exams/student/records/',
            '/exams/wrong/',
        ]
        for url in protected:
            resp = c.get(url, follow=False)
            self.assertEqual(resp.status_code, 302,
                             f'{url} 教师访问应被装饰器挡下')

    # ------------------------- 学生不能打开不属于自己班级的试卷 --------------------------
    def test_student_cannot_enter_other_class_paper(self):
        # 教师在一个班级中建立课程、试卷
        classroom = ClassRoom.objects.create(
            name='实验班A', head_teacher=self.teacher,
        )
        ClassMember.objects.create(
            classroom=classroom, user=self.teacher, role='teacher')
        course = Course.objects.create(
            classroom=classroom, name='数据结构', teacher=self.teacher)
        paper = ExamPaper.objects.create(
            title='限制试卷', course=course,
            is_published=True, created_by=self.teacher)
        # 学生 alice 不在该班级
        c = Client()
        c.force_login(self.student)
        resp = c.get(f'/exams/student/paper/{paper.id}/', follow=False)
        # is_accessible_to 返回 False → messages.error + redirect
        self.assertEqual(resp.status_code, 302)

    # ------------------------- 教师不能编辑别人创建的试题 --------------------------
    def test_teacher_cannot_edit_other_teacher_question(self):
        other_teacher = _make_user('other_t', UserProfile.ROLE_TEACHER)
        q = Question.objects.create(
            type='single_choice', content='1+1=?', answer='A', score=5,
            created_by=other_teacher,
        )
        c = Client()
        c.force_login(self.teacher)
        resp = c.get(f'/exams/questions/{q.id}/edit/', follow=False)
        # 视图通过 created_by 过滤 → 404
        self.assertEqual(resp.status_code, 404)

    # ------------------------- 管理员能进大部分页面 --------------------------
    def test_admin_can_access_admin_site(self):
        c = Client()
        c.force_login(self.admin_user)
        resp = c.get('/exams/', follow=False)  # dashboard 自适配角色
        self.assertEqual(resp.status_code, 200)


class RoleLoginValidationTests(TestCase):
    """登录表单校验：用户必须选择正确的角色才能登录成功。"""

    @classmethod
    def setUpTestData(cls):
        cls.student = _make_user('stu01', UserProfile.ROLE_STUDENT, 'pw12345678')

    def test_login_with_wrong_role_is_rejected(self):
        c = Client()
        resp = c.post('/users/login/', {
            'username': 'stu01', 'password': 'pw12345678',
            'role': 'teacher',        # 故意选错
        }, follow=False)
        # 登录失败应留在登录页（200），未形成 session
        self.assertEqual(resp.status_code, 200)
        # 校验未登录
        resp2 = c.get('/exams/', follow=False)
        self.assertEqual(resp2.status_code, 302)

    def test_login_with_correct_role_succeeds(self):
        c = Client()
        resp = c.post('/users/login/', {
            'username': 'stu01', 'password': 'pw12345678',
            'role': 'student',
        }, follow=False)
        self.assertEqual(resp.status_code, 302)  # 成功后跳 dashboard
        # 已登录访问 dashboard 应返回 200
        resp2 = c.get('/exams/', follow=False)
        self.assertEqual(resp2.status_code, 200)


class CourseAnnouncementPermissionTests(TestCase):
    """课程公告权限：只有授课教师/班主任可发布。"""

    @classmethod
    def setUpTestData(cls):
        cls.head = _make_user('head_t', UserProfile.ROLE_TEACHER)
        cls.student = _make_user('stu_a', UserProfile.ROLE_STUDENT)
        cls.outsider_stu = _make_user('outsider', UserProfile.ROLE_STUDENT)
        cls.classroom = ClassRoom.objects.create(
            name='班级A', head_teacher=cls.head)
        ClassMember.objects.create(
            classroom=cls.classroom, user=cls.head, role='teacher')
        ClassMember.objects.create(
            classroom=cls.classroom, user=cls.student, role='student')
        cls.course = Course.objects.create(
            classroom=cls.classroom, name='算法', teacher=cls.head)

    def test_student_cannot_post_announcement(self):
        c = Client()
        c.force_login(self.student)
        resp = c.post(
            f'/classes/course/{self.course.id}/announce/new/',
            {'title': 'X', 'content': 'Y'}, follow=False,
        )
        # 权限检查会 redirect；且不产生新公告
        self.assertEqual(CourseAnnouncement.objects.count(), 0)

    def test_head_teacher_can_post_announcement(self):
        c = Client()
        c.force_login(self.head)
        resp = c.post(
            f'/classes/course/{self.course.id}/announce/new/',
            {'title': 'HelloClass', 'content': '下周考试'}, follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(CourseAnnouncement.objects.count(), 1)

    def test_outsider_student_cannot_view_course(self):
        c = Client()
        c.force_login(self.outsider_stu)
        resp = c.get(f'/classes/course/{self.course.id}/', follow=False)
        # 非成员：redirect 到我的班级列表
        self.assertEqual(resp.status_code, 302)


class DiscussionPermissionTests(TestCase):
    """讨论区：仅课程成员可参与。"""

    @classmethod
    def setUpTestData(cls):
        cls.teacher = _make_user('t1', UserProfile.ROLE_TEACHER)
        cls.stu_in = _make_user('s1', UserProfile.ROLE_STUDENT)
        cls.stu_out = _make_user('s2', UserProfile.ROLE_STUDENT)
        cls.classroom = ClassRoom.objects.create(
            name='班级B', head_teacher=cls.teacher)
        ClassMember.objects.create(
            classroom=cls.classroom, user=cls.teacher, role='teacher')
        ClassMember.objects.create(
            classroom=cls.classroom, user=cls.stu_in, role='student')
        cls.course = Course.objects.create(
            classroom=cls.classroom, name='操作系统', teacher=cls.teacher)
        cls.topic = DiscussionTopic.objects.create(
            course=cls.course, title='第一次讨论',
            content='大家好', author=cls.teacher)

    def test_member_can_reply_topic(self):
        c = Client()
        c.force_login(self.stu_in)
        resp = c.post(
            f'/classes/course/{self.course.id}/topic/{self.topic.id}/',
            {'content': '老师好！'}, follow=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.topic.replies.count(), 1)

    def test_outsider_cannot_see_topic(self):
        c = Client()
        c.force_login(self.stu_out)
        resp = c.get(
            f'/classes/course/{self.course.id}/topic/{self.topic.id}/',
            follow=False,
        )
        self.assertEqual(resp.status_code, 302)

