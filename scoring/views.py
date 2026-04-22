"""scoring 模块保留为通用工具占位。

实际批阅入口已迁移到 `exams.views.grade_record`，此处保留一个重定向。
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def correct_exam(request, record_id):
    return redirect('exams:grade_record', record_id=record_id)
