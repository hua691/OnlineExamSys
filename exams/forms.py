from django import forms

from classes.models import Course

from .models import ExamPaper, Question


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'subject', 'type', 'content', 'options',
            'answer', 'score', 'explanation',
            'keyword_points', 'similarity_threshold',
        ]
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '如：数据结构',
            }),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control',
                                              'placeholder': '题目正文'}),
            'options': forms.Textarea(attrs={
                'rows': 4, 'class': 'form-control',
                'placeholder': '单/多选题格式（每行一个）：\nA.选项1\nB.选项2\n判断题留空',
            }),
            'answer': forms.Textarea(attrs={
                'rows': 2, 'class': 'form-control',
                'placeholder': '多选题用逗号分隔，如 A,B；判断题填 对/错',
            }),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'explanation': forms.Textarea(attrs={
                'rows': 3, 'class': 'form-control',
                'placeholder': '题目解析（学生在错题集查看）',
            }),
            'keyword_points': forms.Textarea(attrs={
                'rows': 3, 'class': 'form-control', 'style': 'font-family:monospace;',
                'placeholder': '主观题关键词（JSON 数组，可选），如：\n[{"keyword":"递归","weight":0.5},{"keyword":"栈","weight":0.5}]',
            }),
            'similarity_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.1', 'min': 0, 'max': 1,
            }),
        }


class ExamPaperForm(forms.ModelForm):
    class Meta:
        model = ExamPaper
        fields = ['title', 'description', 'duration', 'deadline',
                  'course', 'questions', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 5}),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local',
            }),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'questions': forms.SelectMultiple(attrs={
                'class': 'form-control', 'size': 12,
                'style': 'height: auto;',
            }),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': '试卷标题',
            'description': '试卷描述',
            'duration': '考试时长（分钟）',
            'deadline': '截止时间（留空表示长期有效）',
            'course': '所属课程（选择后学生在该课程内看到试卷）',
            'questions': '选择试题（按住 Ctrl / Shift 多选）',
            'is_published': '立即发布',
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher is not None:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher)
            self.fields['course'].required = False
            self.fields['course'].empty_label = '（公共试卷：无课程关联）'
            self.fields['questions'].queryset = Question.objects.filter(created_by=teacher)
