from django.db import models
from django.conf import settings
from courses.models import Course

# from django.db import models
# from django.conf import settings
from django.utils import timezone


class Exam(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
    ]

    title = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_exams')
    duration_minutes = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    shuffle_questions = models.BooleanField(default=False)
    shuffle_choices = models.BooleanField(default=False)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    invigilators = models.ManyToManyField(            
        'accounts.InvigilatorProfile',                
        blank=True,
        related_name='assigned_exams',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} — {self.course.code}'

    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return self.status == 'published' and self.start_time <= now <= self.end_time
    


class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('short', 'Short Answer'),
        ('essay', 'Essay'),
    ]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES, default='mcq')
    marks = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='question_images/', blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'Q{self.order}: {self.text[:60]}'


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.text} ({"correct" if self.is_correct else "wrong"})'


class ExamSession(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='sessions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)
    is_auto_submitted = models.BooleanField(default=False)
    time_remaining = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ['exam', 'student']

    def __str__(self):
        return f'{self.student.get_full_name()} — {self.exam.title}'