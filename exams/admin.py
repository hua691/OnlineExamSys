from django.contrib import admin

from .models import AnswerRecord, ExamPaper, ExamRecord, Question, WrongQuestion


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['content_short', 'type', 'subject', 'score', 'created_by', 'created_at']
    list_filter = ['type', 'subject', 'created_at']
    search_fields = ['content', 'answer', 'subject']
    readonly_fields = ['created_at']

    def content_short(self, obj):
        return obj.content[:40] + '…' if len(obj.content) > 40 else obj.content
    content_short.short_description = '题目'


@admin.register(ExamPaper)
class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'duration', 'total_score',
                    'created_by', 'is_published', 'created_at']
    list_filter = ['is_published', 'created_at', 'course']
    search_fields = ['title', 'description']
    filter_horizontal = ['questions']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ExamRecord)
class ExamRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'paper', 'status',
                    'objective_score', 'subjective_score', 'score',
                    'start_time', 'end_time']
    list_filter = ['status', 'start_time']
    readonly_fields = ['start_time', 'end_time']
    search_fields = ['student__username', 'paper__title']


@admin.register(AnswerRecord)
class AnswerRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'record', 'question', 'score', 'auto_score',
                    'is_correct', 'similarity', 'created_at']
    list_filter = ['is_correct', 'created_at']
    search_fields = ['record__student__username', 'question__content']


@admin.register(WrongQuestion)
class WrongQuestionAdmin(admin.ModelAdmin):
    list_display = ['student', 'question', 'is_favorite', 'created_at']
    list_filter = ['is_favorite', 'created_at']
    search_fields = ['student__username', 'question__content']
