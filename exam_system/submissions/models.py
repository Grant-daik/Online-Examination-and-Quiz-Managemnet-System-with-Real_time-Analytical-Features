from django.db import models
from django.conf import settings
from exams.models import ExamSession, Question, Choice


class Submission(models.Model):
    session = models.OneToOneField(ExamSession, on_delete=models.CASCADE, related_name='submission')
    total_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade = models.CharField(max_length=5, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.session.student.get_full_name()} — {self.session.exam.title} ({self.grade})'


class Answer(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True, related_name='answers')
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    marks_awarded = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ['submission', 'question']

    def __str__(self):
        return f'Answer to Q{self.question.order} — {self.submission.session.student.get_full_name()}'
    
class SavedAnswer(models.Model):
    """
    Stores answers in progress as the student works through the exam.
    Gets converted to Answer records on final submission.
    """
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='saved_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['session', 'question']

    def __str__(self):
        return f'Draft answer — {self.session.student.get_full_name()} Q{self.question.order}'