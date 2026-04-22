from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    """试题模型（补充字段别名，兼容QUESTION_TYPES引用）"""
    TYPE_CHOICES = QUESTION_TYPES = (
        ('single_choice', '单选题'),
        ('multiple_choice', '多选题'),
        ('judgment', '判断题'),
        ('short_answer', '简答题'),
    )
    # 客观题类型常量，方便判断
    OBJECTIVE_TYPES = ('single_choice', 'multiple_choice', 'judgment')
    SUBJECTIVE_TYPES = ('short_answer',)

    type = models.CharField('题型', max_length=20, choices=TYPE_CHOICES)
    subject = models.CharField('科目/学科', max_length=60, blank=True, default='',
                               help_text='如：数据结构、高等数学')
    content = models.TextField('题目内容')
    options = models.TextField('选项', blank=True, null=True,
                               help_text='每行一个，如：A.选项1')
    answer = models.TextField('标准答案', help_text='多选题用英文逗号分隔，如 A,B')
    score = models.FloatField('分值', default=5.0)
    explanation = models.TextField('题目讲解', blank=True, default='',
                                    help_text='教师添加的错题讲解，学生在错题集中可见')
    # 主观题关键词评分点：JSON 文本，格式: [{"keyword": "...", "weight": 0.4}, ...]
    keyword_points = models.TextField(
        '主观题关键词得分点', blank=True, default='',
        help_text='JSON 数组，例如 [{"keyword":"循环","weight":0.5}]'
    )
    # 相似度阈值（仅主观题有意义）：>=此值时给满分；低于 0.3 给 0；中间按比例
    similarity_threshold = models.FloatField(
        '主观题相似度阈值', default=0.6,
        help_text='0-1，越高评分越严格',
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建人')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '试题'
        verbose_name_plural = '试题'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_type_display()}] {self.content[:50]}'

    @property
    def is_objective(self) -> bool:
        return self.type in self.OBJECTIVE_TYPES

class ExamPaper(models.Model):
    """试卷模型。"""
    title = models.CharField('试卷标题', max_length=200)
    description = models.TextField('试卷描述', blank=True, null=True)
    duration = models.IntegerField('考试时长（分钟）', default=60)
    questions = models.ManyToManyField(Question, verbose_name='包含试题')
    is_published = models.BooleanField('是否发布', default=False)
    # 截止日期：学生"我的待办"根据此字段倒计时；为空视为长期有效
    deadline = models.DateTimeField(
        '截止时间', null=True, blank=True,
        help_text='过期后学生不可再作答；留空表示无截止',
    )
    # 关联到课程（可选；无课程时为"公共试卷"，所有已登录学生均可见）
    course = models.ForeignKey(
        'classes.Course', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='papers',
        verbose_name='所属课程',
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建人')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '试卷'
        verbose_name_plural = '试卷'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def total_score(self) -> float:
        agg = self.questions.aggregate(total=models.Sum('score'))
        return float(agg['total'] or 0)

    def is_accessible_to(self, user) -> bool:
        """判断某个学生是否可以看到/做这张试卷。"""
        if not self.is_published:
            return False
        if self.course_id is None:
            return True  # 公共试卷
        # 有课程约束时：学生必须在该课程所在班级
        from classes.models import ClassMember
        return ClassMember.objects.filter(
            classroom_id=self.course.classroom_id,
            user=user, role='student',
        ).exists()

class ExamRecord(models.Model):
    """考试记录模型（学生答题记录）。"""
    STATUS_CHOICES = (
        ('unfinished', '未完成'),
        ('finished',   '已提交待批阅'),
        ('graded',     '批阅完成'),
    )
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_records')
    paper = models.ForeignKey('ExamPaper', on_delete=models.CASCADE, related_name='exam_records')
    # 客观题得分
    objective_score = models.FloatField('客观题得分', default=0)
    # 主观题得分
    subjective_score = models.FloatField('主观题得分', default=0)
    score = models.FloatField('总得分', null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unfinished')
    # 防作弊：记录学生切换标签页/窗口失焦次数
    switch_tab_count = models.PositiveIntegerField('切屏次数', default=0)

    class Meta:
        unique_together = ('student', 'paper')

    def __str__(self):
        return f'{self.student.username} - {self.paper.title} - {self.get_status_display()}'

    @property
    def needs_manual_grading(self) -> bool:
        """是否还存在未定分的主观题。"""
        return self.answers.filter(
            question__type__in=Question.SUBJECTIVE_TYPES, score__isnull=True,
        ).exists()


class AnswerRecord(models.Model):
    """学生答题详情。"""
    record = models.ForeignKey(
        ExamRecord, on_delete=models.CASCADE,
        related_name='answers', verbose_name='考试记录',
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='试题')
    student_answer = models.TextField('学生答案', blank=True, null=True)
    is_correct = models.BooleanField('是否正确', null=True, blank=True)
    similarity = models.FloatField('语义相似度', null=True, blank=True,
                                    help_text='仅主观题：0-1')
    score = models.FloatField('该题得分', blank=True, null=True)
    auto_score = models.FloatField('自动给分（建议分）', blank=True, null=True)
    created_at = models.DateTimeField('答题时间', auto_now_add=True)

    class Meta:
        verbose_name = '答题记录'
        verbose_name_plural = '答题记录'
        unique_together = ('record', 'question')

    def __str__(self):
        return f'{self.record.student.username} - {self.question.content[:20]}'


class WrongQuestion(models.Model):
    """学生错题本。提交后自动归集客观题错题；主观题批阅后未满分也计入。"""
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='wrong_questions',
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # 关联的答题记录（便于追溯当时的错误答案）
    answer_record = models.ForeignKey(
        AnswerRecord, on_delete=models.CASCADE,
        null=True, blank=True, related_name='wrong_entries',
    )
    is_favorite = models.BooleanField('重点收藏', default=False)
    note = models.TextField('学生备注', blank=True, default='')
    created_at = models.DateTimeField('加入时间', auto_now_add=True)

    class Meta:
        verbose_name = '错题'
        verbose_name_plural = '错题'
        unique_together = ('student', 'question')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student.username} 错题：{self.question.content[:20]}'