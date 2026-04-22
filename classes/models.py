"""班级与课程模型。

参考长江雨课堂的结构：
  - ClassRoom  （班级）：由教师作为"班主任"创建；学生通过邀请码加入；
  - Course     （课程）：挂在某个班级下，每门课程由一位授课教师负责；
  - ClassMember（班级成员）：维护学生加入班级的多对多关系；
  - CourseEnrollment（听课关系）：学生选修某门课；教师加入班级后可创建课程并发布试卷。
"""
import secrets
import string

from django.conf import settings
from django.db import models


def _generate_code(length: int = 6) -> str:
    """生成不含易混淆字符的邀请码。"""
    alphabet = ''.join(c for c in (string.ascii_uppercase + string.digits)
                       if c not in 'O0I1')
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class ClassRoom(models.Model):
    """班级 / 班级。"""
    name = models.CharField('班级名称', max_length=80)
    description = models.TextField('班级简介', blank=True, default='')
    grade = models.CharField('年级', max_length=40, blank=True, default='')
    head_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='headed_classes',
        verbose_name='班主任',
    )
    invite_code = models.CharField('邀请码', max_length=12, unique=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    # 成员：通过 ClassMember 中间表维护；区分学生、任课教师
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ClassMember',
        related_name='joined_classes',
        blank=True,
    )

    class Meta:
        verbose_name = '班级'
        verbose_name_plural = '班级'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.invite_code:
            for _ in range(20):
                code = _generate_code(6)
                if not ClassRoom.objects.filter(invite_code=code).exists():
                    self.invite_code = code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name}（{self.invite_code}）'

    @property
    def student_count(self) -> int:
        return self.memberships.filter(role='student').count()

    @property
    def teacher_count(self) -> int:
        return self.memberships.filter(role='teacher').count()


class ClassMember(models.Model):
    """班级成员关系。"""
    ROLE_CHOICES = (
        ('student', '学生'),
        ('teacher', '任课教师'),
    )
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='class_memberships',
    )
    role = models.CharField('在班角色', max_length=10, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField('加入时间', auto_now_add=True)

    class Meta:
        verbose_name = '班级成员'
        verbose_name_plural = '班级成员'
        unique_together = ('classroom', 'user')
        ordering = ['-joined_at']

    def __str__(self):
        return f'{self.user.username} - {self.classroom.name} ({self.get_role_display()})'


class Course(models.Model):
    """课程：隶属于某个班级，由一位教师授课。"""
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE,
        related_name='courses', verbose_name='所属班级',
    )
    name = models.CharField('课程名称', max_length=80)
    description = models.TextField('课程简介', blank=True, default='')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teaching_courses',
        verbose_name='授课教师',
    )
    cover_color = models.CharField(
        '封面主题色', max_length=20, default='#1677ff',
        help_text='如 #1677ff，用于课程卡片主色',
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '课程'
        verbose_name_plural = '课程'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.classroom.name}'

    @property
    def student_count(self) -> int:
        # 所有班级学生自动加入课程视为听课
        return self.classroom.memberships.filter(role='student').count()

    @property
    def paper_count(self) -> int:
        return self.papers.count()


# ======================================================================
# 课程公告 / 讨论区 （对齐雨课堂课程内页多 Tab 结构）
# ======================================================================
class CourseAnnouncement(models.Model):
    """课程公告。由授课教师/班主任发布，所在班级学生可见。"""
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='announcements',
        verbose_name='所属课程',
    )
    title = models.CharField('公告标题', max_length=120)
    content = models.TextField('公告内容')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='course_announcements', verbose_name='发布者',
    )
    is_pinned = models.BooleanField('置顶', default=False)
    created_at = models.DateTimeField('发布时间', auto_now_add=True)

    class Meta:
        verbose_name = '课程公告'
        verbose_name_plural = '课程公告'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f'[{self.course.name}] {self.title}'


class DiscussionTopic(models.Model):
    """讨论区主题帖（学生/教师均可发布）。"""
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='topics',
        verbose_name='所属课程',
    )
    title = models.CharField('主题标题', max_length=150)
    content = models.TextField('主题内容')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='discussion_topics', verbose_name='发帖人',
    )
    created_at = models.DateTimeField('发布时间', auto_now_add=True)

    class Meta:
        verbose_name = '讨论主题'
        verbose_name_plural = '讨论主题'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.course.name}] {self.title}'

    @property
    def reply_count(self) -> int:
        return self.replies.count()


class DiscussionReply(models.Model):
    """讨论帖的回复。"""
    topic = models.ForeignKey(
        DiscussionTopic, on_delete=models.CASCADE, related_name='replies',
        verbose_name='所属主题',
    )
    content = models.TextField('回复内容')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='discussion_replies', verbose_name='回复人',
    )
    created_at = models.DateTimeField('回复时间', auto_now_add=True)

    class Meta:
        verbose_name = '讨论回复'
        verbose_name_plural = '讨论回复'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author.username} 回复 {self.topic.title}'
