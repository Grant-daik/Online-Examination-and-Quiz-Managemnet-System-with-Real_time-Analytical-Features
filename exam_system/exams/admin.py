from django.contrib import admin
from .models import Exam, Question, Choice, ExamSession


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'status', 'start_time', 'end_time', 'created_by']
    list_filter = ['status', 'course__department']
    search_fields = ['title', 'course__code']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'exam', 'question_type', 'marks', 'order']
    list_filter = ['question_type', 'exam']
    inlines = [ChoiceInline]


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'started_at', 'is_submitted', 'is_auto_submitted']
    list_filter = ['is_submitted', 'is_auto_submitted']