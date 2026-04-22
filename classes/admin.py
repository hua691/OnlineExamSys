from django.contrib import admin

from .models import (ClassMember, ClassRoom, Course, CourseAnnouncement,
                     DiscussionReply, DiscussionTopic)


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade', 'head_teacher', 'invite_code',
                    'student_count', 'teacher_count', 'created_at']
    search_fields = ['name', 'invite_code', 'head_teacher__username']
    list_filter = ['grade', 'created_at']
    readonly_fields = ['invite_code', 'created_at']


@admin.register(ClassMember)
class ClassMemberAdmin(admin.ModelAdmin):
    list_display = ['classroom', 'user', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['classroom__name', 'user__username']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'classroom', 'teacher', 'paper_count',
                    'student_count', 'created_at']
    search_fields = ['name', 'classroom__name', 'teacher__username']
    list_filter = ['created_at']


@admin.register(CourseAnnouncement)
class CourseAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'author', 'is_pinned', 'created_at']
    list_filter = ['is_pinned', 'created_at']
    search_fields = ['title', 'course__name']


@admin.register(DiscussionTopic)
class DiscussionTopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'author', 'reply_count', 'created_at']
    search_fields = ['title', 'course__name']
    list_filter = ['created_at']


@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = ['topic', 'author', 'created_at']
    search_fields = ['topic__title']
    list_filter = ['created_at']
