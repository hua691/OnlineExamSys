from django import forms
from django.db.models import Q

from .models import (ClassRoom, Course, CourseAnnouncement, DiscussionReply,
                     DiscussionTopic)


class ClassRoomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = ['name', 'grade', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control',
                                            'placeholder': '如：计算机2101班'}),
            'grade': forms.TextInput(attrs={'class': 'form-control',
                                             'placeholder': '如：2021级'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                  'placeholder': '班级简介（可选）'}),
        }


class JoinClassForm(forms.Form):
    invite_code = forms.CharField(
        label='邀请码', max_length=12,
        widget=forms.TextInput(attrs={'class': 'form-control',
                                       'placeholder': '请输入 6 位班级邀请码',
                                       'style': 'text-transform:uppercase;letter-spacing:3px;'}),
    )

    def clean_invite_code(self):
        code = self.cleaned_data['invite_code'].strip().upper()
        if not ClassRoom.objects.filter(invite_code=code).exists():
            raise forms.ValidationError('邀请码无效，请向班主任确认')
        return code


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['classroom', 'name', 'description', 'cover_color']
        widgets = {
            'classroom': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control',
                                            'placeholder': '如：数据结构'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cover_color': forms.TextInput(attrs={'class': 'form-control',
                                                   'type': 'color',
                                                   'style': 'height:44px;padding:4px;'}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher is not None:
            # 只允许在教师已加入的班级 / 自己担任班主任的班级创建课程
            self.fields['classroom'].queryset = ClassRoom.objects.filter(
                Q(memberships__user=teacher, memberships__role='teacher') |
                Q(head_teacher=teacher)
            ).distinct()


class CourseAnnouncementForm(forms.ModelForm):
    class Meta:
        model = CourseAnnouncement
        fields = ['title', 'content', 'is_pinned']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '公告标题'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 5,
                'placeholder': '请输入公告内容……'}),
        }


class DiscussionTopicForm(forms.ModelForm):
    class Meta:
        model = DiscussionTopic
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': '讨论主题'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 5,
                'placeholder': '展开你的想法，大家一起讨论……'}),
        }


class DiscussionReplyForm(forms.ModelForm):
    class Meta:
        model = DiscussionReply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': '回复本主题……'}),
        }
