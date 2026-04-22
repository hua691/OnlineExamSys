from django.urls import path

from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard_alias'),

    # 学生
    path('student/todo/', views.my_todo, name='my_todo'),
    path('student/papers/', views.student_paper_list, name='student_paper_list'),
    path('student/paper/<int:paper_id>/', views.exam_paper_detail, name='exam_paper_detail'),
    path('student/paper/<int:paper_id>/submit/', views.submit_exam, name='submit_exam'),
    path('student/paper/<int:paper_id>/autosave/', views.autosave_answer, name='autosave_answer'),
    path('student/records/', views.student_record_list, name='student_record_list'),
    path('result/<int:record_id>/', views.exam_result, name='exam_result'),

    # 学生错题集
    path('wrong/', views.wrong_question_list, name='wrong_question_list'),
    path('wrong/<int:wq_id>/favorite/', views.wrong_question_toggle, name='wrong_favorite'),
    path('wrong/<int:wq_id>/delete/', views.wrong_question_delete, name='wrong_delete'),

    # 教师 - 试题
    path('questions/', views.question_list, name='question_list'),
    path('questions/create/', views.question_create, name='question_create'),
    path('questions/<int:qid>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:qid>/delete/', views.question_delete, name='question_delete'),

    # 教师 - 试卷
    path('papers/', views.paper_list, name='paper_list'),
    path('papers/create/', views.paper_create, name='paper_create'),
    path('papers/<int:paper_id>/edit/', views.paper_edit, name='paper_edit'),
    path('papers/<int:paper_id>/delete/', views.paper_delete, name='paper_delete'),

    # 教师 - 阅卷
    path('teacher/correction/', views.teacher_correction, name='teacher_correction'),
    path('teacher/correction/<int:record_id>/', views.grade_record, name='grade_record'),
    path('teacher/export-records.xlsx', views.export_records_xlsx, name='export_records_xlsx'),
    path('teacher/paper/<int:paper_id>/stats/', views.paper_stats, name='paper_stats'),
]
