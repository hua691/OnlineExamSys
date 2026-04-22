from django.contrib import admin

from .models import ScoringRule, SubjectiveScore


@admin.register(ScoringRule)
class ScoringRuleAdmin(admin.ModelAdmin):
    list_display = ['question_type', 'similarity_threshold', 'weight', 'created_at']
    list_filter = ['question_type']
    readonly_fields = ['created_at']


@admin.register(SubjectiveScore)
class SubjectiveScoreAdmin(admin.ModelAdmin):
    list_display = ['record', 'question', 'similarity',
                    'auto_score', 'manual_score', 'graded_by', 'graded_at']
    list_filter = ['graded_at']
    search_fields = ['record__paper__title', 'question__content', 'graded_by__username']
    readonly_fields = ['graded_at']
