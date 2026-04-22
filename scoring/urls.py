from django.urls import path
from . import views

app_name = 'scoring'

urlpatterns = [
    # 批阅试卷
    path('correct/<int:record_id>/', views.correct_exam, name='correct_exam'),
]