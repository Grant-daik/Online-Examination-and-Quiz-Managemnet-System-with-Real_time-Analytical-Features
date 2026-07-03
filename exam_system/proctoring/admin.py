from django.contrib import admin
from .models import ProctoringLog, Snapshot


@admin.register(ProctoringLog)
class ProctoringLogAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'event_type', 'timestamp', 'get_exam']
    list_filter = ['event_type']
    readonly_fields = ['session', 'event_type', 'timestamp', 'details']

    def get_student(self, obj):
        return obj.session.student.get_full_name()
    get_student.short_description = 'Student'

    def get_exam(self, obj):
        return obj.session.exam.title
    get_exam.short_description = 'Exam'


@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    list_display = ['get_student', 'captured_at', 'flagged', 'flag_reason']
    list_filter = ['flagged']

    def get_student(self, obj):
        return obj.session.student.get_full_name()
    get_student.short_description = 'Student'