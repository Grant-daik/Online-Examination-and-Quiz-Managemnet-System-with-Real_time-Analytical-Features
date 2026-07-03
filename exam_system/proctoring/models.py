from django.db import models
from exams.models import ExamSession


class ProctoringLog(models.Model):
    EVENT_TYPE_CHOICES = [
        ('tab_switch', 'Tab Switch'),
        ('focus_loss', 'Focus Loss'),
        ('copy_attempt', 'Copy Attempt'),
        ('paste_attempt', 'Paste Attempt'),
        ('right_click', 'Right Click Attempt'),
        ('fullscreen_exit', 'Fullscreen Exit'),
        ('multiple_faces', 'Multiple Faces Detected'),
        ('no_face', 'No Face Detected'),
        ('suspicious_movement', 'Suspicious Movement'),
    ]

    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='proctoring_logs')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.session.student.get_full_name()} — {self.event_type} at {self.timestamp}'


class Snapshot(models.Model):
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='snapshots')
    image = models.ImageField(upload_to='snapshots/%Y/%m/%d/')
    captured_at = models.DateTimeField(auto_now_add=True)
    flagged = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-captured_at']

    def __str__(self):
        return f'Snapshot — {self.session.student.get_full_name()} at {self.captured_at}'