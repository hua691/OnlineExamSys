from django.urls import path
from . import views, admin_views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # 管理员自制后台（朱红风格，对应 Django admin 的用户/班级/课程/试卷）
    path('manage/users/', admin_views.manage_users, name='manage_users'),
    path('manage/users/new/', admin_views.create_user, name='create_user'),
    path('manage/users/<int:user_id>/edit/',
         admin_views.edit_user, name='edit_user'),
    path('manage/users/<int:user_id>/toggle/',
         admin_views.toggle_user_active, name='toggle_user_active'),
    path('manage/users/<int:user_id>/role/',
         admin_views.change_user_role, name='change_user_role'),
    path('manage/users/<int:user_id>/reset-pwd/',
         admin_views.reset_user_password, name='reset_user_password'),

    path('manage/classes/', admin_views.manage_classes, name='manage_classes'),
    path('manage/classes/<int:class_id>/delete/',
         admin_views.delete_class, name='delete_class'),

    path('manage/courses/', admin_views.manage_courses, name='manage_courses'),
    path('manage/courses/<int:course_id>/delete/',
         admin_views.delete_course, name='delete_course'),

    path('manage/papers/', admin_views.manage_papers, name='manage_papers'),
    path('manage/papers/<int:paper_id>/publish/',
         admin_views.toggle_paper_publish, name='toggle_paper_publish'),
    path('manage/papers/<int:paper_id>/delete/',
         admin_views.delete_paper, name='delete_paper'),

    # 系统通知广播
    path('manage/broadcast/', admin_views.broadcast_notice, name='broadcast_notice'),
]