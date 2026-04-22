"""班级/课程视图。

学生：加入班级 → 查看"我听的课" → 点课看试卷
教师：创建班级 → 创建课程 → 发布试卷 → 查看班级学生与成绩
"""
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Min, Q
from django.shortcuts import get_object_or_404, redirect, render

from users.decorators import role_required, teacher_required
from users.models import UserProfile

from .forms import (ClassRoomForm, CourseAnnouncementForm, CourseForm,
                    DiscussionReplyForm, DiscussionTopicForm, JoinClassForm)
from .models import (ClassMember, ClassRoom, Course, CourseAnnouncement,
                     DiscussionReply, DiscussionTopic)


def _get_role(user):
    profile = getattr(user, 'profile', None)
    return getattr(profile, 'role', None)


@login_required
def my_classes(request):
    """我的班级（学生侧：我听的课；教师侧：我教的课/班）。"""
    role = _get_role(request.user)

    memberships = ClassMember.objects.filter(user=request.user).select_related('classroom')
    headed_classes = ClassRoom.objects.filter(head_teacher=request.user)

    # 课程列表：学生看自己所在班级所有课程；教师看自己教的课程
    if role == 'teacher':
        courses = Course.objects.filter(teacher=request.user).select_related('classroom')
    else:
        class_ids = memberships.values_list('classroom_id', flat=True)
        courses = Course.objects.filter(classroom_id__in=class_ids).select_related('classroom', 'teacher')

    context = {
        'role': role,
        'memberships': memberships,
        'headed_classes': headed_classes,
        'courses': courses,
    }
    return render(request, 'classes/my_classes.html', context)


@login_required
def join_class(request):
    """学生/教师都可以通过邀请码加入班级。"""
    role = _get_role(request.user)
    if role not in ('student', 'teacher'):
        messages.error(request, '当前账号不支持加入班级')
        return redirect('exams:dashboard')

    if request.method == 'POST':
        form = JoinClassForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['invite_code']
            classroom = ClassRoom.objects.get(invite_code=code)
            # 班主任本人不需要再加入
            if classroom.head_teacher_id == request.user.id:
                messages.info(request, '你是本班班主任，默认已在班级内')
                return redirect('classes:class_detail', class_id=classroom.id)
            member, created = ClassMember.objects.get_or_create(
                classroom=classroom, user=request.user,
                defaults={'role': role},
            )
            if created:
                messages.success(request, f'已成功加入班级：{classroom.name}')
            else:
                messages.info(request, '你已经在该班级内')
            return redirect('classes:class_detail', class_id=classroom.id)
    else:
        form = JoinClassForm()

    return render(request, 'classes/join_class.html', {'form': form, 'role': role})


@teacher_required
def create_class(request):
    """教师创建班级（自己成为班主任）。"""
    if request.method == 'POST':
        form = ClassRoomForm(request.POST)
        if form.is_valid():
            classroom = form.save(commit=False)
            classroom.head_teacher = request.user
            classroom.save()
            # 创建者自动作为任课教师写入成员表
            ClassMember.objects.get_or_create(
                classroom=classroom, user=request.user,
                defaults={'role': 'teacher'},
            )
            messages.success(request, f'班级创建成功！邀请码：{classroom.invite_code}')
            return redirect('classes:class_detail', class_id=classroom.id)
    else:
        form = ClassRoomForm()
    return render(request, 'classes/create_class.html', {'form': form})


@login_required
def class_detail(request, class_id):
    """班级详情。"""
    classroom = get_object_or_404(ClassRoom, id=class_id)
    role = _get_role(request.user)

    # 成员资格校验
    is_head = (classroom.head_teacher_id == request.user.id)
    is_member = ClassMember.objects.filter(classroom=classroom, user=request.user).exists()
    if not (is_head or is_member or role == 'admin'):
        messages.error(request, '你不在该班级，无法查看')
        return redirect('classes:my_classes')

    memberships = classroom.memberships.select_related('user', 'user__profile').all()
    students = [m for m in memberships if m.role == 'student']
    teachers = [m for m in memberships if m.role == 'teacher']
    courses = classroom.courses.select_related('teacher').all()

    is_teacher_in_class = is_head or (role == 'teacher' and is_member)

    context = {
        'classroom': classroom,
        'students': students,
        'teachers': teachers,
        'courses': courses,
        'is_head': is_head,
        'is_teacher_in_class': is_teacher_in_class,
        'role': role,
    }
    return render(request, 'classes/class_detail.html', context)


@teacher_required
def create_course(request):
    """教师在自己所在班级下创建课程。"""
    if request.method == 'POST':
        form = CourseForm(request.POST, teacher=request.user)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, f'课程《{course.name}》创建成功')
            return redirect('classes:course_detail', course_id=course.id)
    else:
        form = CourseForm(teacher=request.user)
    return render(request, 'classes/create_course.html', {'form': form})


def _course_access(request, course):
    """课程访问权限 + 身份判断。返回 (role, is_course_teacher) 或 None(无权)。"""
    role = _get_role(request.user)
    is_head = (course.classroom.head_teacher_id == request.user.id)
    is_member = ClassMember.objects.filter(
        classroom=course.classroom, user=request.user,
    ).exists()
    is_course_teacher = (course.teacher_id == request.user.id) or is_head
    if not (is_head or is_member or is_course_teacher or role == 'admin'):
        return None
    return role, is_course_teacher


@login_required
def course_detail(request, course_id):
    """课程详情（雨课堂式多 Tab：试卷 / 公告 / 讨论 / 成绩单）。

    通过 query string ?tab=papers|announcements|discussions|scores 切换。
    """
    course = get_object_or_404(Course, id=course_id)
    access = _course_access(request, course)
    if access is None:
        messages.error(request, '你不属于该课程所在班级')
        return redirect('classes:my_classes')
    role, is_course_teacher = access

    tab = request.GET.get('tab', 'papers')
    if tab not in ('papers', 'announcements', 'discussions', 'scores'):
        tab = 'papers'

    # 延迟导入，避免 classes <-> exams 循环
    from exams.models import ExamPaper, ExamRecord

    papers = ExamPaper.objects.filter(course=course).order_by('-created_at')
    my_records = {}
    if role == 'student':
        rec_qs = ExamRecord.objects.filter(student=request.user, paper__in=papers)
        my_records = {r.paper_id: r for r in rec_qs}

    announcements = course.announcements.select_related('author').all()
    topics = course.topics.select_related('author').annotate(
        reply_cnt=Count('replies')
    )

    # "成绩单" Tab 数据
    score_rows = []
    if tab == 'scores':
        if role == 'student':
            # 学生：自己的所有成绩
            recs = ExamRecord.objects.filter(
                student=request.user, paper__course=course,
            ).select_related('paper').order_by('-start_time')
            score_rows = [{
                'paper': r.paper, 'student': request.user, 'record': r,
            } for r in recs]
        else:
            # 教师/管理员：班级所有学生成绩
            recs = ExamRecord.objects.filter(
                paper__course=course,
            ).select_related('paper', 'student', 'student__profile').order_by(
                '-start_time')
            score_rows = [{
                'paper': r.paper, 'student': r.student, 'record': r,
            } for r in recs]

    context = {
        'course': course,
        'role': role,
        'is_course_teacher': is_course_teacher,
        'tab': tab,
        # papers tab
        'papers': papers,
        'my_records': my_records,
        # announcements tab
        'announcements': announcements,
        # discussions tab
        'topics': topics,
        # scores tab
        'score_rows': score_rows,
    }
    return render(request, 'classes/course_detail.html', context)


# ----------------------------------------------------------------
# 课程公告
# ----------------------------------------------------------------
@login_required
def announcement_create(request, course_id):
    """教师/班主任发布课程公告。"""
    course = get_object_or_404(Course, id=course_id)
    access = _course_access(request, course)
    if access is None:
        messages.error(request, '无权访问该课程')
        return redirect('classes:my_classes')
    _, is_course_teacher = access
    if not is_course_teacher:
        messages.error(request, '仅授课教师/班主任可发布公告')
        return redirect('classes:course_detail', course_id=course.id)

    if request.method == 'POST':
        form = CourseAnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.course = course
            ann.author = request.user
            ann.save()
            messages.success(request, '公告发布成功')
            return redirect(f'/classes/course/{course.id}/?tab=announcements')
    else:
        form = CourseAnnouncementForm()
    return render(request, 'classes/announcement_form.html',
                  {'form': form, 'course': course})


@login_required
def announcement_delete(request, course_id, ann_id):
    """删除公告（仅作者或班主任/管理员可操作）。"""
    course = get_object_or_404(Course, id=course_id)
    ann = get_object_or_404(CourseAnnouncement, id=ann_id, course=course)
    role = _get_role(request.user)
    is_head = (course.classroom.head_teacher_id == request.user.id)
    if not (ann.author_id == request.user.id or is_head or role == 'admin'):
        messages.error(request, '无权删除该公告')
        return redirect('classes:course_detail', course_id=course.id)
    ann.delete()
    messages.success(request, '公告已删除')
    return redirect(f'/classes/course/{course.id}/?tab=announcements')


# ----------------------------------------------------------------
# 讨论区：主题 & 回复
# ----------------------------------------------------------------
@login_required
def topic_create(request, course_id):
    """班级成员均可在课程讨论区发帖。"""
    course = get_object_or_404(Course, id=course_id)
    access = _course_access(request, course)
    if access is None:
        messages.error(request, '你不属于该课程所在班级')
        return redirect('classes:my_classes')

    if request.method == 'POST':
        form = DiscussionTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.course = course
            topic.author = request.user
            topic.save()
            messages.success(request, '讨论主题已发布')
            return redirect('classes:topic_detail',
                            course_id=course.id, topic_id=topic.id)
    else:
        form = DiscussionTopicForm()
    return render(request, 'classes/topic_form.html',
                  {'form': form, 'course': course})


@login_required
def topic_detail(request, course_id, topic_id):
    """讨论主题详情与回帖。"""
    course = get_object_or_404(Course, id=course_id)
    access = _course_access(request, course)
    if access is None:
        messages.error(request, '你不属于该课程所在班级')
        return redirect('classes:my_classes')
    topic = get_object_or_404(DiscussionTopic, id=topic_id, course=course)

    if request.method == 'POST':
        form = DiscussionReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.topic = topic
            reply.author = request.user
            reply.save()
            return redirect('classes:topic_detail',
                            course_id=course.id, topic_id=topic.id)
    else:
        form = DiscussionReplyForm()

    replies = topic.replies.select_related('author', 'author__profile').all()
    return render(request, 'classes/topic_detail.html', {
        'course': course, 'topic': topic, 'replies': replies, 'form': form,
    })


@login_required
def topic_delete(request, course_id, topic_id):
    """删除讨论主题（仅作者或教师/管理员）。"""
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(DiscussionTopic, id=topic_id, course=course)
    role = _get_role(request.user)
    is_head = (course.classroom.head_teacher_id == request.user.id)
    is_course_teacher = (course.teacher_id == request.user.id) or is_head
    if not (topic.author_id == request.user.id or is_course_teacher or role == 'admin'):
        messages.error(request, '无权删除该主题')
        return redirect('classes:topic_detail',
                        course_id=course.id, topic_id=topic.id)
    topic.delete()
    messages.success(request, '讨论主题已删除')
    return redirect(f'/classes/course/{course.id}/?tab=discussions')


@role_required('teacher', 'admin')
def class_stats(request, class_id):
    """班级成绩统计：整体得分、平均/最高/最低、题型正确率、错题分布。"""
    from exams.models import AnswerRecord, ExamRecord, Question  # 延迟导入
    classroom = get_object_or_404(ClassRoom, id=class_id)

    # 权限：班主任 或 任课教师 或 admin
    role = _get_role(request.user)
    is_head = (classroom.head_teacher_id == request.user.id)
    is_teacher_in_class = ClassMember.objects.filter(
        classroom=classroom, user=request.user, role='teacher',
    ).exists()
    if not (is_head or is_teacher_in_class or role == 'admin'):
        messages.error(request, '无权查看该班级统计')
        return redirect('classes:my_classes')

    student_ids = ClassMember.objects.filter(
        classroom=classroom, role='student'
    ).values_list('user_id', flat=True)

    # 统计口径:客观题已出分即可纳入(status in finished/graded),避免只算已批阅的导致数据稀疏
    records = ExamRecord.objects.filter(
        paper__course__classroom=classroom,
        student_id__in=student_ids,
        status__in=['finished', 'graded'],
    ).select_related('student', 'paper')

    # 汇总
    agg = records.aggregate(
        avg=Avg('score'), max=Max('score'), min=Min('score'), cnt=Count('id')
    )

    # 按试卷分组
    paper_stats = defaultdict(lambda: {'paper': None, 'scores': []})
    for r in records:
        s = paper_stats[r.paper_id]
        s['paper'] = r.paper
        if r.score is not None:
            s['scores'].append(float(r.score))
    paper_rows = []
    for pid, v in paper_stats.items():
        scores = v['scores']
        if not scores:
            continue
        paper_rows.append({
            'paper': v['paper'],
            'count': len(scores),
            'avg': round(sum(scores) / len(scores), 2),
            'max': max(scores),
            'min': min(scores),
        })
    paper_rows.sort(key=lambda x: x['paper'].created_at, reverse=True)

    # 题型正确率：按 Answer 记录评估 is_correct
    ans_qs = AnswerRecord.objects.filter(record__in=records).select_related('question')
    by_type = defaultdict(lambda: {'total': 0, 'correct': 0})
    wrong_counter = defaultdict(lambda: {'q': None, 'wrong': 0})
    for a in ans_qs:
        q = a.question
        by_type[q.type]['total'] += 1
        if a.score is not None and a.score >= q.score:
            by_type[q.type]['correct'] += 1
        else:
            wrong_counter[q.id]['q'] = q
            wrong_counter[q.id]['wrong'] += 1

    type_map = dict(Question.TYPE_CHOICES)
    type_rows = []
    for t, v in by_type.items():
        if v['total'] == 0:
            continue
        type_rows.append({
            'type': type_map.get(t, t),
            'total': v['total'],
            'correct': v['correct'],
            'rate': round(v['correct'] * 100 / v['total'], 1),
        })

    wrong_rows = [
        {'question': v['q'], 'wrong': v['wrong']}
        for v in wrong_counter.values() if v['q'] is not None
    ]
    wrong_rows.sort(key=lambda x: x['wrong'], reverse=True)
    wrong_rows = wrong_rows[:10]

    # 导出 CSV
    if request.GET.get('export') == 'csv':
        import csv
        from django.http import HttpResponse
        resp = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        resp['Content-Disposition'] = f'attachment; filename=class_{class_id}_stats.csv'
        resp.write('\ufeff')  # BOM for Excel
        writer = csv.writer(resp)
        writer.writerow(['类型', '试卷/题型', '数量', '平均分/正确率', '最高', '最低'])
        for p in paper_rows:
            writer.writerow(['试卷', p['paper'].title, p['count'],
                             p['avg'], p['max'], p['min']])
        for t in type_rows:
            writer.writerow(['题型', t['type'], t['total'],
                             f"{t['rate']}%", '', ''])
        return resp

    context = {
        'classroom': classroom,
        'agg': agg,
        'paper_rows': paper_rows,
        'type_rows': type_rows,
        'wrong_rows': wrong_rows,
        'student_count': len(student_ids),
    }
    return render(request, 'classes/class_stats.html', context)


@role_required('teacher', 'admin')
def student_detail(request, class_id, student_id):
    """班级学生个人档案：历史答题、得分趋势。"""
    from django.contrib.auth.models import User
    from exams.models import ExamRecord
    classroom = get_object_or_404(ClassRoom, id=class_id)
    student = get_object_or_404(User, id=student_id)

    # 权限：班主任或班级任课教师
    role = _get_role(request.user)
    is_head = (classroom.head_teacher_id == request.user.id)
    is_teacher_in_class = ClassMember.objects.filter(
        classroom=classroom, user=request.user, role='teacher',
    ).exists()
    if not (is_head or is_teacher_in_class or role == 'admin'):
        messages.error(request, '无权查看该学生')
        return redirect('classes:class_detail', class_id=class_id)

    records = ExamRecord.objects.filter(
        student=student,
        paper__course__classroom=classroom,
    ).select_related('paper', 'paper__course').order_by('start_time')

    # 得分趋势:只要有分就画点(finished 显示客观分,graded 显示总分)
    trend = []
    for r in records:
        if r.score is not None and r.status in ('finished', 'graded'):
            trend.append({
                'time': r.end_time.strftime('%Y-%m-%d') if r.end_time else '-',
                'score': float(r.score),
                'paper': r.paper.title,
            })

    context = {
        'classroom': classroom,
        'student': student,
        'records': records,
        'trend': trend,
    }
    return render(request, 'classes/student_detail.html', context)
