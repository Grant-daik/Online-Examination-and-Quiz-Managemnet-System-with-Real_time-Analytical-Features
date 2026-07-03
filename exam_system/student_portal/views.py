from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from exams.models import Exam, ExamSession
from exams.utils import get_shuffled_questions, get_shuffled_choices, calculate_total_marks
from submissions.models import Submission, SavedAnswer
from submissions.utils import grade_submission
from notifications.models import Notification

import json
from django.views.decorators.http import require_POST


def student_required(view_func):
    """Decorator to restrict views to students only."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'student':
            messages.error(request, 'Access denied. Students only.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@student_required
def dashboard(request):
    student = request.user
    now = timezone.now()

    # exams available to the student based on enrolled courses
    try:
        enrolled_courses = student.student_profile.enrolled_courses.all()
    except Exception:
        enrolled_courses = []

    available_exams = Exam.objects.filter(
        course__in=enrolled_courses,
        status='published',
        start_time__lte=now,
        end_time__gte=now,
    )

    upcoming_exams = Exam.objects.filter(
        course__in=enrolled_courses,
        status='published',
        start_time__gt=now,
    ).order_by('start_time')[:5]

    # exams the student has already attempted
    attempted_sessions = ExamSession.objects.filter(
        student=student,
        is_submitted=True,
    ).select_related('exam', 'submission')

    unread_notifications = Notification.objects.filter(
        recipient=student,
        is_read=False,
    ).order_by('-created_at')[:5]

    return render(request, 'student/dashboard.html', {
        'available_exams': available_exams,
        'upcoming_exams': upcoming_exams,
        'attempted_sessions': attempted_sessions,
        'unread_notifications': unread_notifications,
    })


@student_required
def exam_list(request):
    student = request.user
    now = timezone.now()

    try:
        enrolled_courses = student.student_profile.enrolled_courses.all()
    except Exception:
        enrolled_courses = []

    exams = Exam.objects.filter(
        course__in=enrolled_courses,
        status='published',
    ).order_by('start_time')

    print("CURRENT TIME:", now)

    for exam in exams:
        exam.session = ExamSession.objects.filter(
            exam=exam,
            student=student
        ).first()

        print(
            "TITLE:", exam.title,
            "| START:", exam.start_time,
            "| END:", exam.end_time,
            "| START > NOW:", exam.start_time > now
        )

    return render(request, 'student/exam_list.html', {
        'exams': exams,
        'now': now,
    })



@student_required
def start_exam(request, exam_id):
    student = request.user
    exam = get_object_or_404(Exam, id=exam_id, status='published')
    now = timezone.now()

    # check exam window
    if now < exam.start_time:
        messages.error(request, 'This exam has not started yet.')
        return redirect('student:exam_list')

    if now > exam.end_time:
        messages.error(request, 'This exam has already ended.')
        return redirect('student:exam_list')

    # check if student already has a session
    session = ExamSession.objects.filter(exam=exam, student=student).first()

    if session:
        if session.is_submitted:
            messages.info(request, 'You have already submitted this exam.')
            return redirect('student:result_detail', submission_id=session.submission.id)
        # resume existing session
        return redirect('student:take_exam', session_id=session.id)

    # create a new session
    session = ExamSession.objects.create(
        exam=exam,
        student=student,
        time_remaining=exam.duration_minutes * 60,
    )

    messages.success(request, f'Exam started. You have {exam.duration_minutes} minutes.')
    return redirect('student:take_exam', session_id=session.id)


@student_required
def take_exam(request, session_id):
    student = request.user
    session = get_object_or_404(ExamSession, id=session_id, student=student)

    # redirect if already submitted
    if session.is_submitted:
        messages.info(request, 'You have already submitted this exam.')
        return redirect('student:result_detail', submission_id=session.submission.id)

    exam = session.exam
    now = timezone.now()

    # force submit if exam window has closed
    if now > exam.end_time and not session.is_submitted:
        submission = grade_submission(session)
        messages.warning(request, 'Time is up. Your exam has been auto-submitted.')
        return redirect('student:result_detail', submission_id=submission.id)

    questions = get_shuffled_questions(exam)

    # attach choices and any saved answers to each question
    saved_answers = {
        sa.question_id: sa
        for sa in SavedAnswer.objects.filter(session=session)
    }

    for question in questions:
        question.display_choices = get_shuffled_choices(question)
        question.saved = saved_answers.get(question.id)

    return render(request, 'student/take_exam.html', {
        'session': session,
        'exam': exam,
        'questions': questions,
        'time_remaining': session.time_remaining or exam.duration_minutes * 60,
    })


@student_required
def submit_exam(request, session_id):
    if request.method != 'POST':
        return redirect('student:dashboard')

    student = request.user
    session = get_object_or_404(ExamSession, id=session_id, student=student)

    if session.is_submitted:
        messages.info(request, 'This exam has already been submitted.')
        return redirect('student:result_detail', submission_id=session.submission.id)

    # save all answers from POST data before grading
    exam = session.exam
    for question in exam.questions.all():
        choice_id = request.POST.get(f'question_{question.id}')
        text_answer = request.POST.get(f'text_{question.id}', '')

        from exams.models import Choice
        choice = None
        if choice_id:
            try:
                choice = Choice.objects.get(id=choice_id, question=question)
            except Choice.DoesNotExist:
                pass

        SavedAnswer.objects.update_or_create(
            session=session,
            question=question,
            defaults={
                'selected_choice': choice,
                'text_answer': text_answer,
            }
        )

    submission = grade_submission(session)
    messages.success(request, 'Exam submitted successfully!')
    return redirect('student:result_detail', submission_id=submission.id)


@student_required
def result_list(request):
    student = request.user
    submissions = Submission.objects.filter(
        session__student=student
    ).select_related('session__exam', 'session__exam__course').order_by('-submitted_at')

    return render(request, 'student/result_list.html', {'submissions': submissions})


@student_required
def result_detail(request, submission_id):
    student = request.user
    submission = get_object_or_404(
        Submission,
        id=submission_id,
        session__student=student
    )

    answers = submission.answers.select_related(
        'question', 'selected_choice'
    ).prefetch_related('question__choices').order_by('question__order')

    return render(request, 'student/result_detail.html', {
        'submission': submission,
        'answers': answers,
    })




@student_required
@require_POST
def sync_timer(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id, student=request.user)
    try:
        data = json.loads(request.body)
        time_remaining = int(data.get('time_remaining', 0))
        session.time_remaining = time_remaining
        session.save(update_fields=['time_remaining'])
        return JsonResponse({'status': 'ok'})
    except Exception:
        return JsonResponse({'status': 'error'}, status=400)