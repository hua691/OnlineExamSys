"""大规模演示数据:3 个班级 · 20+ 学生 · 5 门课程 · 30+ 试题 · 多张试卷 · 真实答题记录 · 讨论/公告/通知。

运行:python manage.py seed_rich_demo

幂等:重复执行不会重复插入(所有对象用 get_or_create)。
"""
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from classes.models import (ClassMember, ClassRoom, Course,
                            CourseAnnouncement, DiscussionReply, DiscussionTopic)
from exams.models import AnswerRecord, ExamPaper, ExamRecord, Question, WrongQuestion
from notifications.models import Notification, notify
from scoring.utils import subjective_auto_score
from users.models import UserProfile


# ===================== 账号 =====================
ACCOUNTS = [
    # (username, password, role, real_name, student_id)
    ('admin',    'admin123',    'admin',   '系统管理员', ''),
    ('teacher1', 'teacher123',  'teacher', '张老师',   'T001'),
    ('teacher2', 'teacher123',  'teacher', '李老师',   'T002'),
    ('teacher3', 'teacher123',  'teacher', '王老师',   'T003'),
    ('teacher4', 'teacher123',  'teacher', '刘老师',   'T004'),
]
# 20 个学生,跨 3 个年级
STUDENT_NAMES = [
    '王小明', '赵小红', '孙小强', '钱小芳', '李小龙',
    '周小雨', '吴小刚', '郑小燕', '冯小波', '陈小琳',
    '褚小东', '卫小军', '蒋小玉', '沈小秋', '韩小雪',
    '杨小飞', '朱小丽', '秦小柳', '许小杰', '何小美',
]
for i, name in enumerate(STUDENT_NAMES, start=1):
    year = 2021 + (i - 1) % 3
    sid = f'S{year}{i:03d}'
    ACCOUNTS.append((f'student{i}', 'student123', 'student', name, sid))


# ===================== 班级 / 课程 =====================
CLASSROOMS = [
    # (name, grade, desc, head_teacher_username)
    ('计算机2101班', '2021级', '计算机科学与技术专业实验班', 'teacher1'),
    ('软件工程2202班', '2022级', '软件工程专业卓越班',      'teacher2'),
    ('信息安全2301班', '2023级', '信息安全专业',          'teacher3'),
]

COURSES = [
    # (classroom_name, course_name, teacher_username, color, desc)
    ('计算机2101班', '数据结构',     'teacher1', '#1677ff', '线性结构、树、图、排序等基础算法'),
    ('计算机2101班', '数据库原理',   'teacher2', '#722ed1', '关系模型、SQL、事务、范式'),
    ('计算机2101班', '计算机网络',   'teacher3', '#13c2c2', 'OSI 模型、TCP/IP、HTTP、路由'),
    ('软件工程2202班', '操作系统',   'teacher3', '#fa541c', '进程、线程、内存管理、文件系统'),
    ('软件工程2202班', '软件工程导论', 'teacher4', '#52c41a', '需求分析、设计、测试、敏捷'),
    ('信息安全2301班', '密码学基础', 'teacher4', '#eb2f96', '对称加密、公钥加密、数字签名、哈希'),
]


# ===================== 试题 =====================
QUESTIONS = [
    # 数据结构
    dict(subject='数据结构', type='single_choice',
         content='下列数据结构中,属于非线性结构的是？',
         options='A.栈\nB.队列\nC.二叉树\nD.链表',
         answer='C', score=5.0,
         explanation='栈、队列、链表是线性结构;二叉树是典型非线性结构。'),
    dict(subject='数据结构', type='single_choice',
         content='栈的特点是？',
         options='A.先进先出\nB.后进先出\nC.随机访问\nD.链式存储',
         answer='B', score=5.0,
         explanation='栈(Stack)遵循后进先出(LIFO)原则。'),
    dict(subject='数据结构', type='multiple_choice',
         content='下列哪些属于排序算法？',
         options='A.冒泡排序\nB.快速排序\nC.二分查找\nD.归并排序',
         answer='A,B,D', score=6.0,
         explanation='二分查找是搜索算法,不是排序算法。'),
    dict(subject='数据结构', type='judgment',
         content='链表支持随机访问。',
         options='', answer='错', score=4.0,
         explanation='链表只能顺序访问,数组才支持随机访问。'),
    dict(subject='数据结构', type='judgment',
         content='完全二叉树是满二叉树的特例。',
         options='', answer='错', score=4.0,
         explanation='满二叉树是完全二叉树的特例(反之不成立)。'),
    dict(subject='数据结构', type='short_answer',
         content='请简述什么是递归?并举例说明它的应用场景。',
         options='',
         answer='递归是指一个函数在执行过程中直接或间接调用自身的过程。典型应用场景包括:遍历树结构、斐波那契数列、汉诺塔问题、快速排序和归并排序等分治算法、计算阶乘等。',
         score=10.0,
         keyword_points='[{"keyword":"递归","weight":0.3},{"keyword":"调用自身","weight":0.3},{"keyword":"树","weight":0.2},{"keyword":"分治","weight":0.2}]',
         similarity_threshold=0.5,
         explanation='回答应包括:递归定义 + 典型应用场景(树、分治、阶乘等)。'),

    # 数据库
    dict(subject='数据库', type='single_choice',
         content='SQL 中用于过滤分组结果的关键字是?',
         options='A.WHERE\nB.HAVING\nC.GROUP BY\nD.ORDER BY',
         answer='B', score=5.0,
         explanation='HAVING 过滤分组后结果,WHERE 过滤原始记录。'),
    dict(subject='数据库', type='single_choice',
         content='下列哪个不属于数据库三级模式?',
         options='A.外模式\nB.模式\nC.内模式\nD.用户模式',
         answer='D', score=5.0,
         explanation='三级模式:外模式、模式、内模式。'),
    dict(subject='数据库', type='multiple_choice',
         content='下列哪些是关系型数据库?',
         options='A.MySQL\nB.MongoDB\nC.PostgreSQL\nD.Redis',
         answer='A,C', score=6.0,
         explanation='MongoDB 是文档数据库,Redis 是键值数据库。'),
    dict(subject='数据库', type='judgment',
         content='第三范式(3NF)要求所有非主属性完全依赖于主键。',
         options='', answer='错', score=4.0,
         explanation='3NF 要求非主属性不传递依赖于主键;完全依赖是 2NF 的要求。'),
    dict(subject='数据库', type='short_answer',
         content='简述事务的 ACID 特性。',
         options='',
         answer='ACID 指原子性(Atomicity)、一致性(Consistency)、隔离性(Isolation)、持久性(Durability)。原子性要求事务要么全部执行要么全部不执行;一致性保证事务前后数据库状态合法;隔离性指并发事务互不干扰;持久性指事务提交后永久生效。',
         score=10.0,
         keyword_points='[{"keyword":"原子","weight":0.25},{"keyword":"一致","weight":0.25},{"keyword":"隔离","weight":0.25},{"keyword":"持久","weight":0.25}]',
         similarity_threshold=0.5,
         explanation='必须覆盖四项:原子性/一致性/隔离性/持久性。'),

    # 计算机网络
    dict(subject='计算机网络', type='single_choice',
         content='TCP 三次握手第三次发送的是?',
         options='A.SYN\nB.SYN+ACK\nC.ACK\nD.FIN',
         answer='C', score=5.0,
         explanation='TCP 握手:客户端 SYN → 服务端 SYN+ACK → 客户端 ACK。'),
    dict(subject='计算机网络', type='single_choice',
         content='HTTP 默认端口是?',
         options='A.21\nB.22\nC.80\nD.443',
         answer='C', score=4.0,
         explanation='HTTP 默认 80,HTTPS 默认 443。'),
    dict(subject='计算机网络', type='multiple_choice',
         content='下列哪些属于传输层协议?',
         options='A.TCP\nB.IP\nC.UDP\nD.HTTP',
         answer='A,C', score=6.0,
         explanation='IP 是网络层,HTTP 是应用层。'),
    dict(subject='计算机网络', type='judgment',
         content='UDP 提供可靠的数据传输。',
         options='', answer='错', score=4.0,
         explanation='UDP 是无连接、不可靠的协议。'),
    dict(subject='计算机网络', type='short_answer',
         content='简述 TCP 和 UDP 的主要区别。',
         options='',
         answer='TCP 面向连接,提供可靠传输(三次握手建立连接、超时重传、流量控制、拥塞控制);UDP 无连接,不保证可靠,但开销小、实时性好,适合视频会议、直播等。',
         score=10.0,
         keyword_points='[{"keyword":"连接","weight":0.3},{"keyword":"可靠","weight":0.3},{"keyword":"握手","weight":0.2},{"keyword":"开销","weight":0.2}]',
         similarity_threshold=0.5,
         explanation='答案应区分:连接/可靠/握手/开销 四个维度。'),

    # 操作系统
    dict(subject='操作系统', type='single_choice',
         content='下列哪个不属于进程状态?',
         options='A.就绪\nB.运行\nC.阻塞\nD.中断',
         answer='D', score=5.0,
         explanation='进程三态:就绪、运行、阻塞(或等待)。'),
    dict(subject='操作系统', type='multiple_choice',
         content='下列哪些属于页面置换算法?',
         options='A.FIFO\nB.LRU\nC.OPT\nD.SJF',
         answer='A,B,C', score=6.0,
         explanation='SJF 是进程调度算法,不是页面置换。'),
    dict(subject='操作系统', type='judgment',
         content='线程比进程的切换开销更大。',
         options='', answer='错', score=4.0,
         explanation='线程共享地址空间,切换开销比进程小。'),

    # 软件工程
    dict(subject='软件工程', type='single_choice',
         content='下列哪种不是软件开发生命周期模型?',
         options='A.瀑布\nB.螺旋\nC.冒烟\nD.敏捷',
         answer='C', score=5.0,
         explanation='冒烟是一种测试类型,不是生命周期模型。'),
    dict(subject='软件工程', type='multiple_choice',
         content='下列哪些属于敏捷开发方法?',
         options='A.Scrum\nB.XP\nC.Kanban\nD.瀑布',
         answer='A,B,C', score=6.0,
         explanation='瀑布是传统模型,非敏捷。'),
    dict(subject='软件工程', type='short_answer',
         content='简述什么是单元测试,并说明它的价值。',
         options='',
         answer='单元测试是对软件中的最小可测试单元(函数、方法、类)进行独立测试。价值:提高代码质量、及早发现 bug、便于重构、作为文档、支持持续集成。',
         score=8.0,
         keyword_points='[{"keyword":"单元","weight":0.3},{"keyword":"最小","weight":0.2},{"keyword":"bug","weight":0.2},{"keyword":"重构","weight":0.3}]',
         similarity_threshold=0.45,
         explanation='答案应涵盖:单元测试定义 + 至少 2 个价值点。'),

    # 密码学
    dict(subject='密码学', type='single_choice',
         content='下列哪个属于对称加密算法?',
         options='A.RSA\nB.ECC\nC.AES\nD.ElGamal',
         answer='C', score=5.0,
         explanation='AES 是对称;RSA/ECC/ElGamal 是非对称。'),
    dict(subject='密码学', type='multiple_choice',
         content='下列哪些是哈希算法?',
         options='A.SHA-256\nB.RSA\nC.MD5\nD.SHA-1',
         answer='A,C,D', score=6.0,
         explanation='RSA 是公钥加密算法,不是哈希。'),
    dict(subject='密码学', type='judgment',
         content='MD5 在安全场景仍被推荐使用。',
         options='', answer='错', score=4.0,
         explanation='MD5 已被证明不安全,存在碰撞攻击,不再推荐。'),
    dict(subject='密码学', type='short_answer',
         content='简述数字签名的工作原理。',
         options='',
         answer='数字签名使用发送方的私钥对消息摘要进行加密,接收方用发送方的公钥解密验证。保证消息完整性(不可篡改)、发送方身份真实性(不可伪造)、不可抵赖性。',
         score=10.0,
         keyword_points='[{"keyword":"私钥","weight":0.25},{"keyword":"公钥","weight":0.25},{"keyword":"摘要","weight":0.25},{"keyword":"完整性","weight":0.25}]',
         similarity_threshold=0.5,
         explanation='答案应涵盖:私钥签名 + 公钥验签 + 保护的属性。'),

    # 高等数学
    dict(subject='高等数学', type='single_choice',
         content='函数 f(x) = x² 在 x=2 处的导数是?',
         options='A.2\nB.4\nC.8\nD.16',
         answer='B', score=5.0,
         explanation="f'(x)=2x,代入 x=2 得 4。"),
    dict(subject='高等数学', type='judgment',
         content='所有连续函数都可导。',
         options='', answer='错', score=4.0,
         explanation='连续函数不一定可导,如 f(x)=|x| 在 x=0 处不可导。'),
]


# ===================== 试卷定义 =====================
# (title, course_name, created_by_username, is_published, deadline_delta_hours, questions_subjects, desc)
PAPERS = [
    ('《数据结构》第一次随堂测试', '数据结构', 'teacher1', True,  None,  ['数据结构'],
     '覆盖栈、队列、链表、二叉树基本概念'),
    ('《数据结构》期中考试', '数据结构', 'teacher1', True,  24 * 7, ['数据结构'],
     '综合性试卷,6 道题 60 分钟'),
    ('《数据库原理》第一次作业', '数据库原理', 'teacher2', True, None,   ['数据库'],
     'SQL 与关系代数基础'),
    ('《计算机网络》章节测试', '计算机网络', 'teacher3', True, 24 * 3,  ['计算机网络'],
     'TCP/IP 与应用层协议'),
    ('《操作系统》月考', '操作系统', 'teacher3', True,  -24,   ['操作系统'],  # 已过期
     '(注:此卷已过截止时间,用于演示"已截止"状态)'),
    ('《软件工程》期末试卷(草稿)', '软件工程导论', 'teacher4', False, None, ['软件工程'],
     '尚未发布,仅教师可见'),
    ('《密码学》课堂练习', '密码学基础', 'teacher4', True, 24 * 14, ['密码学'],
     '对称/非对称加密 + 数字签名'),
]


# ===================== 公告 & 讨论 =====================
ANNOUNCEMENTS = [
    ('数据结构', '关于期中考试安排',  '各位同学,数据结构期中考试定于下周三下午 14:00,地点计实 301,请携带学生证。', True),
    ('数据结构', '第三章作业提交通知', '请在本周日 23:59 前完成第三章课后习题,逾期不收。', False),
    ('计算机网络', '讲座通知',        '本周五晚 19:00 在逸夫楼举办"5G 核心网技术"讲座,欢迎参加。', True),
    ('密码学基础', '实验补选',       '未完成 RSA 实验的同学请到实验室 2 补选,联系刘老师。', False),
]

TOPICS = [
    ('数据结构', '红黑树和 AVL 树到底有什么区别?', '大家讨论一下,什么场景下应该用红黑树,什么场景用 AVL 树?', [
        ('红黑树插入删除更快,AVL 查询更快。Linux 内核调度用的就是红黑树。', 0),
        ('AVL 严格平衡,红黑树近似平衡,工程中红黑树应用更广。', 1),
    ]),
    ('数据库原理', '索引越多越好吗?', '老师说索引能加快查询,但我听说太多反而不好,怎么权衡?', [
        ('写操作会同步更新索引,太多索引会降低写性能。', 2),
    ]),
    ('计算机网络', 'HTTPS 真的安全吗?', '中间人攻击还可能吗?', [
        ('只要证书信任链是可信的就很难被中间人劫持。', 0),
        ('但弱 CA 被攻破时就会出问题,比如 DigiNotar 事件。', 1),
    ]),
]


class Command(BaseCommand):
    help = '大规模演示数据:3 个班级 · 20+ 学生 · 5 门课程 · 30+ 试题 · 多张试卷 + 真实答题记录。'

    def handle(self, *args, **options):
        with transaction.atomic():
            self._run()

    def _run(self):
        users = self._create_accounts()
        classrooms = self._create_classrooms(users)
        self._add_members(users, classrooms)
        courses = self._create_courses(users, classrooms)
        questions = self._create_questions(users)
        papers = self._create_papers(users, courses, questions)
        self._create_answer_records(users, papers)
        self._create_announcements(users, courses)
        self._create_discussions(users, courses)
        self._create_notifications(users, papers)
        self._print_summary(users, classrooms)

    # ---------- 账号 ----------
    def _create_accounts(self):
        self.stdout.write('[1/8] 创建账号...')
        users = {}
        for username, password, role, real_name, sid in ACCOUNTS:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': real_name,
                    'is_staff': role == 'admin',
                    'is_superuser': username == 'admin',
                },
            )
            if created or not u.check_password(password):
                u.set_password(password)
                u.first_name = real_name
                if username == 'admin':
                    u.is_staff = True
                    u.is_superuser = True
                u.save()
            p, _ = UserProfile.objects.get_or_create(user=u)
            p.role = role
            p.student_id = sid
            p.save()
            users[username] = u
        self.stdout.write(self.style.SUCCESS(f'  [OK] 共 {len(users)} 个账号'))
        return users

    # ---------- 班级 ----------
    def _create_classrooms(self, users):
        self.stdout.write('[2/8] 创建班级...')
        classrooms = {}
        for name, grade, desc, ht in CLASSROOMS:
            cls, _ = ClassRoom.objects.get_or_create(
                name=name,
                defaults={'grade': grade, 'description': desc,
                          'head_teacher': users[ht]},
            )
            classrooms[name] = cls
        self.stdout.write(self.style.SUCCESS(f'  [OK] 共 {len(classrooms)} 个班级'))
        return classrooms

    # ---------- 班级成员 ----------
    def _add_members(self, users, classrooms):
        self.stdout.write('[3/8] 分配班级成员...')
        # 教师:班主任进自己的班级,其他教师进所有班级(任课)
        all_teachers = [v for k, v in users.items() if k.startswith('teacher')]
        for cls in classrooms.values():
            for t in all_teachers:
                ClassMember.objects.get_or_create(
                    classroom=cls, user=t, defaults={'role': 'teacher'})

        # 学生:按顺序均分到 3 个班
        students = [v for k, v in users.items() if k.startswith('student')]
        cls_list = list(classrooms.values())
        for i, s in enumerate(students):
            cls = cls_list[i % len(cls_list)]
            ClassMember.objects.get_or_create(
                classroom=cls, user=s, defaults={'role': 'student'})
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] {len(students)} 学生分到 {len(cls_list)} 班级'))

    # ---------- 课程 ----------
    def _create_courses(self, users, classrooms):
        self.stdout.write('[4/8] 创建课程...')
        courses = {}
        for cls_name, name, teacher, color, desc in COURSES:
            course, _ = Course.objects.get_or_create(
                classroom=classrooms[cls_name], name=name,
                defaults={'teacher': users[teacher],
                          'cover_color': color, 'description': desc},
            )
            courses[name] = course
        self.stdout.write(self.style.SUCCESS(f'  [OK] 共 {len(courses)} 门课程'))
        return courses

    # ---------- 试题 ----------
    def _create_questions(self, users):
        self.stdout.write('[5/8] 创建试题...')
        # 题目的 created_by 轮流分给 4 个教师
        teachers = [users[f'teacher{i}'] for i in range(1, 5)]
        qs_by_subject = {}
        for i, qd in enumerate(QUESTIONS):
            q, _ = Question.objects.get_or_create(
                content=qd['content'],
                defaults={**qd, 'created_by': teachers[i % len(teachers)]},
            )
            qs_by_subject.setdefault(qd['subject'], []).append(q)
        total = sum(len(v) for v in qs_by_subject.values())
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] {total} 道试题 / {len(qs_by_subject)} 个科目'))
        return qs_by_subject

    # ---------- 试卷 ----------
    def _create_papers(self, users, courses, questions):
        self.stdout.write('[6/8] 创建试卷...')
        now = timezone.now()
        papers = []
        for title, course_name, teacher, published, hours, subjects, desc in PAPERS:
            deadline = now + timedelta(hours=hours) if hours is not None else None
            paper, created = ExamPaper.objects.get_or_create(
                title=title,
                defaults={
                    'description': desc,
                    'duration': 60,
                    'course': courses[course_name],
                    'created_by': users[teacher],
                    'is_published': published,
                    'deadline': deadline,
                },
            )
            if created:
                # 按 subjects 归集题目
                qlist = []
                for s in subjects:
                    qlist.extend(questions.get(s, []))
                paper.questions.set(qlist)
            papers.append(paper)
        self.stdout.write(self.style.SUCCESS(f'  [OK] 共 {len(papers)} 张试卷'))
        return papers

    # ---------- 答题记录 (核心:生成真实成绩) ----------
    def _create_answer_records(self, users, papers):
        self.stdout.write('[7/8] 生成学生答题记录...')
        rng = random.Random(42)  # 固定种子,结果稳定
        # 挑选已发布且未过期的前两张试卷,让 6-10 个学生作答
        target_papers = [p for p in papers if p.is_published
                         and (p.deadline is None or p.deadline > timezone.now())][:3]
        students = [v for k, v in users.items() if k.startswith('student')]

        count = 0
        for paper in target_papers:
            # 只让该课程班级里的学生作答
            if paper.course:
                member_ids = ClassMember.objects.filter(
                    classroom=paper.course.classroom, role='student',
                ).values_list('user_id', flat=True)
                eligible = [s for s in students if s.id in member_ids]
            else:
                eligible = students
            if not eligible:
                continue

            # 让 60% 的学生提交
            sample = rng.sample(eligible, k=max(1, int(len(eligible) * 0.6)))
            for stu in sample:
                record, created = ExamRecord.objects.get_or_create(
                    student=stu, paper=paper,
                )
                if not created and record.status != 'unfinished':
                    continue  # 已有记录,跳过重复生成

                obj_total = 0.0
                subj_total = 0.0
                for q in paper.questions.all():
                    accurate = rng.random() < 0.75  # 75% 答对概率
                    if q.type == 'single_choice':
                        student_ans = q.answer if accurate else rng.choice(['A', 'B', 'C', 'D'])
                    elif q.type == 'multiple_choice':
                        student_ans = q.answer if accurate else rng.choice(['A', 'B', 'A,B', 'A,C'])
                    elif q.type == 'judgment':
                        student_ans = q.answer if accurate else ('错' if q.answer == '对' else '对')
                    else:  # short_answer
                        # 生成一个"接近标准答案"的回答(去掉一些关键词随机化相似度)
                        if accurate:
                            student_ans = q.answer[:max(30, int(len(q.answer) * 0.7))]
                        else:
                            student_ans = '不太记得了,简单说几句。' + q.answer[:20]

                    is_correct = None
                    similarity = None
                    auto_score = 0.0

                    if q.type in Question.OBJECTIVE_TYPES:
                        # 客观题评分:严格比较
                        if q.type == 'multiple_choice':
                            std = set(q.answer.replace(' ', '').split(','))
                            got = set(student_ans.replace(' ', '').split(','))
                            is_correct = (std == got)
                        else:
                            is_correct = (student_ans.strip() == q.answer.strip())
                        auto_score = q.score if is_correct else 0.0
                        obj_total += auto_score
                        score = auto_score
                    else:
                        # 主观题:AI 评分 + 教师认可建议分作为最终分
                        similarity, auto_score = subjective_auto_score(q, student_ans)
                        is_correct = auto_score >= q.score
                        score = auto_score
                        subj_total += score

                    AnswerRecord.objects.update_or_create(
                        record=record, question=q,
                        defaults={
                            'student_answer': student_ans,
                            'is_correct': is_correct,
                            'similarity': similarity,
                            'auto_score': auto_score,
                            'score': score,
                        },
                    )

                # 只要存在主观题,约 70% 概率 graded,其余 finished(等待批阅,演示用)
                has_subj = paper.questions.filter(
                    type__in=Question.SUBJECTIVE_TYPES).exists()
                if has_subj and rng.random() < 0.3:
                    record.status = 'finished'
                    record.score = obj_total  # 暂记客观分
                else:
                    record.status = 'graded'
                    record.score = round(obj_total + subj_total, 2)
                record.objective_score = round(obj_total, 2)
                record.subjective_score = round(subj_total, 2)
                record.end_time = timezone.now() - timedelta(
                    minutes=rng.randint(5, 60 * 24))
                record.save()

                # 同步错题
                for ans in record.answers.all():
                    got = ans.score if ans.score is not None else 0
                    if got < ans.question.score:
                        WrongQuestion.objects.get_or_create(
                            student=stu, question=ans.question,
                            defaults={'answer_record': ans},
                        )
                count += 1
        self.stdout.write(self.style.SUCCESS(
            f'  [OK] 生成 {count} 份答题记录(含真实分数)'))

    # ---------- 公告 ----------
    def _create_announcements(self, users, courses):
        self.stdout.write('[8/8] 公告 / 讨论 / 通知...')
        for course_name, title, content, pinned in ANNOUNCEMENTS:
            c = courses.get(course_name)
            if not c:
                continue
            CourseAnnouncement.objects.get_or_create(
                course=c, title=title,
                defaults={'content': content,
                          'author': c.teacher,
                          'is_pinned': pinned},
            )

    # ---------- 讨论 ----------
    def _create_discussions(self, users, courses):
        students = [v for k, v in users.items() if k.startswith('student')]
        for course_name, title, content, replies in TOPICS:
            c = courses.get(course_name)
            if not c:
                continue
            topic, created = DiscussionTopic.objects.get_or_create(
                course=c, title=title,
                defaults={'content': content, 'author': students[0]},
            )
            if created:
                for reply_text, idx in replies:
                    DiscussionReply.objects.create(
                        topic=topic, content=reply_text,
                        author=students[idx % len(students)],
                    )

    # ---------- 通知 ----------
    def _create_notifications(self, users, papers):
        admin = users['admin']
        students = [v for k, v in users.items() if k.startswith('student')]
        teachers = [v for k, v in users.items() if k.startswith('teacher')]

        # 管理员广播 1 条欢迎通知(包含自己)
        for u in list(students) + list(teachers) + [admin]:
            if not Notification.objects.filter(
                    recipient=u, type='generic', title='欢迎使用云阅卷').exists():
                notify(
                    recipient=u, sender=admin, type='generic',
                    title='欢迎使用云阅卷',
                    message='各位老师同学好!长江·云阅卷已上线,课前随堂测、主观题 AI 评分等功能一应俱全。',
                )

        # 给每个学生一条"新试卷发布"提醒
        for paper in papers:
            if not paper.is_published or not paper.course:
                continue
            member_users = User.objects.filter(
                class_memberships__classroom=paper.course.classroom,
                class_memberships__role='student',
            )
            prefix = f'新试卷《{paper.title}'
            existing_recipient_ids = set(Notification.objects.filter(
                type='exam_published', title__startswith=prefix,
            ).values_list('recipient_id', flat=True))
            for u in member_users:
                if u.id in existing_recipient_ids:
                    continue
                notify(
                    recipient=u, sender=paper.created_by,
                    type='exam_published',
                    title=f'新试卷《{paper.title}》已发布',
                    message=f'请在 {paper.duration} 分钟内完成作答',
                    link=f'/exams/student/paper/{paper.id}/',
                )

    # ---------- 输出 ----------
    def _print_summary(self, users, classrooms):
        self.stdout.write(self.style.SUCCESS('\n[OK] 大规模演示数据生成完毕'))
        self.stdout.write('='*60)
        self.stdout.write('管理员   admin    / admin123')
        self.stdout.write('教师 ×4  teacher1-4 / teacher123')
        self.stdout.write('学生 ×20 student1-20 / student123')
        self.stdout.write('-'*60)
        self.stdout.write('班级及邀请码:')
        for cls in classrooms.values():
            count = cls.memberships.filter(role='student').count()
            self.stdout.write(f'  · {cls.name}: 邀请码 {cls.invite_code},{count} 人')
        self.stdout.write('='*60)
