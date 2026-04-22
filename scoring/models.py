"""阅卷相关的辅助模型。"""
from django.db import models

from exams.models import ExamRecord, Question


class ScoringRule(models.Model):
    """阅卷规则（按题型）。"""
    question_type = models.CharField(
        max_length=20,
        choices=Question.TYPE_CHOICES,
        verbose_name='题型',
    )
    similarity_threshold = models.FloatField(default=0.6, verbose_name='相似度阈值')
    weight = models.FloatField(default=1.0, verbose_name='评分权重')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '阅卷规则'
        verbose_name_plural = '阅卷规则'

    def __str__(self):
        return f'{self.get_question_type_display()} - 阈值{self.similarity_threshold}'


class SubjectiveScore(models.Model):
    """主观题评分记录（用于追溯）。"""
    record = models.ForeignKey(
        ExamRecord, on_delete=models.CASCADE,
        related_name='subjective_scores', verbose_name='考试记录',
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='试题')
    similarity = models.FloatField(verbose_name='语义相似度')
    auto_score = models.FloatField(verbose_name='自动建议分')
    manual_score = models.FloatField(verbose_name='人工最终分')
    graded_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name='批阅人')
    graded_at = models.DateTimeField(auto_now_add=True, verbose_name='批阅时间')

    class Meta:
        verbose_name = '主观题评分记录'
        verbose_name_plural = '主观题评分记录'
        unique_together = ('record', 'question')
