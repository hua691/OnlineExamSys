"""种子数据：创建示例管理员/教师/学生，并注入班级/课程/试题/试卷/通知。

运行：python manage.py seed_demo
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from classes.models import ClassMember, ClassRoom, Course
from exams.models import ExamPaper, Question
from notifications.models import notify
from users.models import UserProfile


DEMO_ACCOUNTS = [
    # (username, password, role, real_name, student_id)
    ('admin',   'admin123',   'admin',   '系统管理员', ''),
    ('teacher1','teacher123', 'teacher', '张老师',    'T001'),
    ('teacher2','teacher123', 'teacher', '李老师',    'T002'),
    ('student1','student123', 'student', '王小明',    'S2021001'),
    ('student2','student123', 'student', '赵小红',    'S2021002'),
    ('student3','student123', 'student', '孙小强',    'S2021003'),
]

DEMO_QUESTIONS = [
    dict(type='single_choice', subject='数据结构',
         content='下列数据结构中，属于非线性结构的是？',
         options='A.栈\nB.队列\nC.二叉树\nD.链表',
         answer='C', score=5.0,
         explanation='栈、队列、链表都是线性结构；二叉树是典型非线性结构。'),
    dict(type='single_choice', subject='数据结构',
         content='栈的特点是？',
         options='A.先进先出\nB.后进先出\nC.随机访问\nD.链式存储',
         answer='B', score=5.0,
         explanation='栈（Stack）遵循后进先出（LIFO）原则。'),
    dict(type='multiple_choice', subject='数据结构',
         content='下列哪些属于排序算法？（多选）',
         options='A.冒泡排序\nB.快速排序\nC.二分查找\nD.归并排序',
         answer='A,B,D', score=6.0,
         explanation='二分查找是搜索算法，不是排序算法。'),
    dict(type='judgment', subject='数据结构',
         content='链表支持随机访问。',
         options='', answer='错', score=4.0,
         explanation='链表只能顺序访问，数组才支持随机访问。'),
    dict(type='judgment', subject='数据结构',
         content='完全二叉树是满二叉树的特例。',
         options='', answer='错', score=4.0,
         explanation='满二叉树是完全二叉树的特例（反之不成立）。'),
    dict(type='short_answer', subject='数据结构',
         content='请简述什么是递归？并举例说明它的应用场景。',
         options='',
         answer='递归是指一个函数在执行过程中直接或间接调用自身的过程。典型应用场景包括：遍历树结构、斐波那契数列、汉诺塔问题、快速排序和归并排序等分治算法、计算阶乘等。',
         score=10.0,
         keyword_points='[{"keyword":"递归","weight":0.3},{"keyword":"调用自身","weight":0.3},{"keyword":"树","weight":0.2},{"keyword":"分治","weight":0.2}]',
         similarity_threshold=0.5,
         explanation='回答应当包括：递归定义（函数调用自身）+ 典型应用场景（树、分治、阶乘等）。'),
]


class Command(BaseCommand):
    help = '生成演示数据（管理员/教师/学生 + 班级 + 课程 + 试题 + 试卷）'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('正在创建演示账号...')
        users = {}
        for username, password, role, real_name, sid in DEMO_ACCOUNTS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': real_name, 'is_staff': role == 'admin',
                          'is_superuser': username == 'admin'},
            )
            if created or not user.check_password(password):
                user.set_password(password)
                user.first_name = real_name
                if username == 'admin':
                    user.is_staff = True
                    user.is_superuser = True
                user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.student_id = sid
            profile.save()
            users[username] = user

        self.stdout.write(self.style.SUCCESS('✓ 演示账号已就绪'))

        self.stdout.write('正在创建班级与课程...')
        teacher1 = users['teacher1']
        teacher2 = users['teacher2']
        student1 = users['student1']
        student2 = users['student2']
        student3 = users['student3']

        classroom, _ = ClassRoom.objects.get_or_create(
            name='计算机2101班',
            defaults={'grade': '2021级',
                      'description': '计算机科学与技术专业实验班',
                      'head_teacher': teacher1},
        )
        # 班级成员：班主任 teacher1 + 任课 teacher2 + 3 个学生
        ClassMember.objects.get_or_create(classroom=classroom, user=teacher1,
                                          defaults={'role': 'teacher'})
        ClassMember.objects.get_or_create(classroom=classroom, user=teacher2,
                                          defaults={'role': 'teacher'})
        for s in (student1, student2, student3):
            ClassMember.objects.get_or_create(classroom=classroom, user=s,
                                              defaults={'role': 'student'})

        course, _ = Course.objects.get_or_create(
            classroom=classroom, name='数据结构',
            defaults={'teacher': teacher1,
                      'description': '讲授线性结构、树、图、排序等基础算法',
                      'cover_color': '#1677ff'},
        )
        course2, _ = Course.objects.get_or_create(
            classroom=classroom, name='数据库原理',
            defaults={'teacher': teacher2, 'cover_color': '#722ed1'},
        )
        self.stdout.write(self.style.SUCCESS(
            f'✓ 班级：{classroom.name} | 邀请码：{classroom.invite_code}'))

        self.stdout.write('正在创建试题...')
        questions = []
        for qd in DEMO_QUESTIONS:
            q, _ = Question.objects.get_or_create(
                content=qd['content'], created_by=teacher1,
                defaults=qd,
            )
            questions.append(q)

        self.stdout.write('正在创建试卷...')
        paper, created = ExamPaper.objects.get_or_create(
            title='《数据结构》第一次随堂测试',
            defaults={
                'description': '覆盖栈、队列、链表、二叉树基本概念',
                'duration': 60,
                'course': course,
                'created_by': teacher1,
                'is_published': True,
            },
        )
        if created:
            paper.questions.set(questions)

        self.stdout.write(self.style.SUCCESS('✓ 试卷已就绪'))

        # 给学生发一条欢迎通知
        for s in (student1, student2, student3):
            notify(
                recipient=s, sender=teacher1, type='exam_published',
                title=f'新试卷《{paper.title}》已发布',
                message=f'请在 {paper.duration} 分钟内完成作答',
                link=f'/exams/student/paper/{paper.id}/',
            )
        self.stdout.write(self.style.SUCCESS('✓ 演示数据生成完毕'))
        self.stdout.write('\n======================= 演示账号 =======================')
        self.stdout.write('管理员：admin    / admin123')
        self.stdout.write('教师  ：teacher1 / teacher123   （班主任 张老师）')
        self.stdout.write('教师  ：teacher2 / teacher123   （任课 李老师）')
        self.stdout.write('学生  ：student1 / student123   （王小明）')
        self.stdout.write('学生  ：student2 / student123   （赵小红）')
        self.stdout.write('学生  ：student3 / student123   （孙小强）')
        self.stdout.write(f'班级邀请码：{classroom.invite_code}')
        self.stdout.write('========================================================')
