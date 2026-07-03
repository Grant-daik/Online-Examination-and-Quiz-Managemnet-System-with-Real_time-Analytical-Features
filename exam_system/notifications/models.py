from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIF_TYPE_CHOICES = [
        ('exam_reminder', 'Exam Reminder'),
        ('exam_published', 'Exam Published'),
        ('exam_closed', 'Exam Closed'),
        ('result_released', 'Result Released'),
        ('proctor_alert', 'Proctoring Alert'),
        ('manual_grade', 'Manual Grade Updated'),
        ('general', 'General'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notif_type = models.CharField(max_length=30, choices=NOTIF_TYPE_CHOICES, default='general')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.notif_type} → {self.recipient.get_full_name()} — {self.title}'