"""消息通知。

支持的通知类型：
  - exam_published    ：学生收到新试卷发布提醒
  - exam_submitted    ：教师收到学生提交提醒
  - exam_graded       ：学生收到成绩发布/批阅完成提醒
  - grade_finished    ：教师收到批阅完成反馈
  - class_joined      ：加入班级成功（系统提醒）
  - generic           ：通用消息
"""
from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = (
        ('exam_published', '试卷发布提醒'),
        ('exam_submitted', '学生已提交'),
        ('exam_graded',    '成绩已发布'),
        ('grade_finished', '批阅完成'),
        ('class_joined',   '加入班级'),
        ('generic',        '系统消息'),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='接收人',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sent_notifications',
        verbose_name='发送人',
    )
    type = models.CharField('类型', max_length=30, choices=TYPE_CHOICES, default='generic')
    title = models.CharField('标题', max_length=120)
    message = models.TextField('内容', blank=True, default='')
    link = models.CharField('跳转链接', max_length=255, blank=True, default='')
    is_read = models.BooleanField('已读', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']

    def __str__(self):
        return f'→{self.recipient.username}: {self.title}'


def notify(recipient, title, message='', type='generic', link='', sender=None):
    """便捷的推送工具函数。"""
    if recipient is None:
        return None
    return Notification.objects.create(
        recipient=recipient, sender=sender,
        title=title, message=message, type=type, link=link,
    )
