from django.urls import path

from . import views

app_name = 'classes'

urlpatterns = [
    # 我的班级 / 我听的课 / 我教的课
    path('mine/', views.my_classes, name='my_classes'),
    # 加入班级（通过邀请码）
    path('join/', views.join_class, name='join_class'),
    # 教师创建班级
    path('create/', views.create_class, name='create_class'),
    # 班级详情（学生看：课程/公告；教师看：学生名册 + 课程管理）
    path('<int:class_id>/', views.class_detail, name='class_detail'),
    # 班级学生统计（教师查看班级得分趋势等）
    path('<int:class_id>/stats/', views.class_stats, name='class_stats'),
    # 班级内单个学生的答题历史
    path('<int:class_id>/student/<int:student_id>/',
         views.student_detail, name='student_detail'),

    # 课程相关
    path('course/create/', views.create_course, name='create_course'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),

    # 课程公告
    path('course/<int:course_id>/announce/new/',
         views.announcement_create, name='announcement_create'),
    path('course/<int:course_id>/announce/<int:ann_id>/delete/',
         views.announcement_delete, name='announcement_delete'),

    # 课程讨论区
    path('course/<int:course_id>/topic/new/',
         views.topic_create, name='topic_create'),
    path('course/<int:course_id>/topic/<int:topic_id>/',
         views.topic_detail, name='topic_detail'),
    path('course/<int:course_id>/topic/<int:topic_id>/delete/',
         views.topic_delete, name='topic_delete'),
]
