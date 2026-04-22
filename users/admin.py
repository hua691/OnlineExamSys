from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

# 内联显示 UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '用户档案'

# 扩展内置 User 管理
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# 重新注册 User 模型
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# 注册 UserProfile（可选）
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'student_id']
    list_filter = ['role']
    search_fields = ['user__username', 'student_id']