from django.contrib import admin
from .models import Submission, Answer, SavedAnswer


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ['question', 'selected_choice', 'text_answer', 'is_correct', 'marks_awarded']


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'get_exam', 'total_score', 'total_marks', 'percentage', 'grade', 'submitted_at']
    list_filter = ['grade']
    inlines = [AnswerInline]

    def get_student(self, obj):
        return obj.session.student.get_full_name()
    get_student.short_description = 'Student'

    def get_exam(self, obj):
        return obj.session.exam.title
    get_exam.short_description = 'Exam'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'get_student', 'is_correct', 'marks_awarded']
    list_filter = ['is_correct']

    def get_student(self, obj):
        return obj.submission.session.student.get_full_name()
    get_student.short_description = 'Student'


admin.site.register(SavedAnswer)