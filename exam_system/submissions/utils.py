from django.utils import timezone
from .models import Submission, Answer, SavedAnswer
from exams.models import ExamSession


def calculate_grade(percentage):
    if percentage >= 70:
        return 'A'
    elif percentage >= 60:
        return 'B'
    elif percentage >= 50:
        return 'C'
    elif percentage >= 45:
        return 'D'
    elif percentage >= 40:
        return 'E'
    else:
        return 'F'


def grade_submission(session):
    """
    Auto-grades an exam session.
    - MCQ: marked automatically based on selected choice
    - Short answer / essay: marked as 0 by default, lecturer grades manually
    Called immediately after a student submits or time expires.
    """

    # prevent double grading
    if hasattr(session, 'submission'):
        return session.submission

    answers = []
    total_score = 0
    total_marks = 0

    for question in session.exam.questions.all():
        total_marks += question.marks
        marks_awarded = 0
        is_correct = False
        selected_choice = None
        text_answer = ''

        # try to find the student's saved answer for this question
        saved = SavedAnswer.objects.filter(session=session, question=question).first()

        if saved:
            if question.question_type == 'mcq' and saved.selected_choice:
                selected_choice = saved.selected_choice
                if selected_choice.is_correct:
                    is_correct = True
                    marks_awarded = question.marks
            else:
                text_answer = saved.text_answer or ''

        total_score += marks_awarded

        answers.append(Answer(
            question=question,
            selected_choice=selected_choice,
            text_answer=text_answer,
            is_correct=is_correct,
            marks_awarded=marks_awarded,
        ))

    percentage = (total_score / total_marks * 100) if total_marks > 0 else 0
    grade = calculate_grade(percentage)

    submission = Submission.objects.create(
        session=session,
        total_score=total_score,
        total_marks=total_marks,
        percentage=round(percentage, 2),
        grade=grade,
    )

    for answer in answers:
        answer.submission = submission

    Answer.objects.bulk_create(answers)

    # mark the session as submitted
    session.is_submitted = True
    session.submitted_at = timezone.now()
    session.save()

    return submission


def auto_submit_session(session):
    """
    Called when the exam timer expires.
    Flags the session as auto-submitted before grading.
    """
    session.is_auto_submitted = True
    session.save()
    return grade_submission(session)