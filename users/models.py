from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_TEACHER = 'teacher'
    ROLE_STUDENT = 'student'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = (
        (ROLE_TEACHER, '教师'),
        (ROLE_STUDENT, '学生'),
        (ROLE_ADMIN, '管理员'),
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="关联用户"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
        verbose_name="用户角色"
    )
    student_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="学号"
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = "用户档案"
        verbose_name_plural = "用户档案"

# 增强信号量：自动为所有User创建/补全Profile
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # 无论是否新建用户，都确保有Profile
    profile, created = UserProfile.objects.get_or_create(
        user=instance,
        defaults={'role': UserProfile.ROLE_STUDENT}
    )
    # 如果是新建用户，无需额外操作；如果是更新，保存即可
    profile.save()