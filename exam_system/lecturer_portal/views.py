
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count
from exams.models import Exam, Question, Choice, ExamSession
from exams.utils import calculate_total_marks
from submissions.models import Submission, Answer
from notifications.utils import notify_exam_published
from .forms import ExamForm, QuestionForm, ChoiceFormSet, ManualGradeForm


from decimal import Decimal


def lecturer_required(view_func):
    """Decorator to restrict views to lecturers only."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['lecturer', 'admin']:
            messages.error(request, 'Access denied. Lecturers only.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@lecturer_required
def dashboard(request):
    lecturer = request.user
    exams = Exam.objects.filter(created_by=lecturer).order_by('-created_at')

    total_exams = exams.count()
    active_exams = exams.filter(status='published', start_time__lte=timezone.now(), end_time__gte=timezone.now()).count()
    total_submissions = Submission.objects.filter(session__exam__created_by=lecturer).count()

    recent_exams = exams[:5]
    recent_submissions = Submission.objects.filter(
        session__exam__created_by=lecturer
    ).select_related('session__exam', 'session__student').order_by('-submitted_at')[:5]

    return render(request, 'lecturer/dashboard.html', {
        'total_exams': total_exams,
        'active_exams': active_exams,
        'total_submissions': total_submissions,
        'recent_exams': recent_exams,
        'recent_submissions': recent_submissions,
    })


@lecturer_required
def exam_list(request):
    exams = Exam.objects.filter(created_by=request.user).order_by('-created_at')

    # annotate each exam with submission count
    for exam in exams:
        exam.submission_count = Submission.objects.filter(session__exam=exam).count()
        exam.question_count = exam.questions.count()

    return render(request, 'lecturer/exam_list.html', {'exams': exams})


@lecturer_required
def create_exam(request):
    form = ExamForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            messages.success(request, f'Exam "{exam.title}" created successfully. Now add your questions.')
            return redirect('lecturer:add_question', exam_id=exam.id)
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'lecturer/create_exam.html', {'form': form})


@lecturer_required
def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    questions = exam.questions.prefetch_related('choices').order_by('order')
    total_marks = calculate_total_marks(exam)
    submission_count = Submission.objects.filter(session__exam=exam).count()

    return render(request, 'lecturer/exam_detail.html', {
        'exam': exam,
        'questions': questions,
        'total_marks': total_marks,
        'submission_count': submission_count,
    })


@lecturer_required
def edit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)

    if exam.status == 'published':
        messages.error(request, 'You cannot edit a published exam.')
        return redirect('lecturer:exam_detail', exam_id=exam.id)

    form = ExamForm(request.POST or None, instance=exam)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Exam updated successfully.')
            return redirect('lecturer:exam_detail', exam_id=exam.id)

    return render(request, 'lecturer/create_exam.html', {
        'form': form,
        'exam': exam,
        'editing': True,
    })


@lecturer_required
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)

    if exam.status == 'published':
        messages.error(request, 'You cannot delete a published exam.')
        return redirect('lecturer:exam_detail', exam_id=exam.id)

    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted.')
        return redirect('lecturer:exam_list')

    return render(request, 'lecturer/confirm_delete.html', {'exam': exam})


@lecturer_required
def publish_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)

    if exam.questions.count() == 0:
        messages.error(request, 'You cannot publish an exam with no questions.')
        return redirect('lecturer:exam_detail', exam_id=exam.id)

    if request.method == 'POST':
        exam.status = 'published'
        exam.save()
        notify_exam_published(exam)
        messages.success(request, f'"{exam.title}" is now published and visible to students.')
        return redirect('lecturer:exam_detail', exam_id=exam.id)

    return render(request, 'lecturer/confirm_publish.html', {'exam': exam})


@lecturer_required
def close_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)

    if request.method == 'POST':
        exam.status = 'closed'
        exam.save()
        messages.success(request, f'"{exam.title}" has been closed.')
        return redirect('lecturer:exam_detail', exam_id=exam.id)

    return render(request, 'lecturer/confirm_close.html', {'exam': exam})


@lecturer_required
def add_question(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)

    question_form = QuestionForm(request.POST or None, request.FILES or None)
    choice_formset = ChoiceFormSet(request.POST or None)

    if request.method == 'POST':
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.exam = exam
            question.save()

            if question.question_type == 'mcq':
                choice_formset = ChoiceFormSet(request.POST, instance=question)
                if choice_formset.is_valid():
                    choice_formset.save()

            messages.success(request, 'Question added.')

            if 'add_another' in request.POST:
                return redirect('lecturer:add_question', exam_id=exam.id)
            return redirect('lecturer:exam_detail', exam_id=exam.id)
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'lecturer/add_question.html', {
        'exam': exam,
        'question_form': question_form,
        'choice_formset': choice_formset,
    })


@lecturer_required
def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id, exam__created_by=request.user)
    exam = question.exam

    question_form = QuestionForm(request.POST or None, request.FILES or None, instance=question)
    choice_formset = ChoiceFormSet(request.POST or None, instance=question)

    if request.method == 'POST':
        if question_form.is_valid() and choice_formset.is_valid():
            question_form.save()
            choice_formset.save()
            messages.success(request, 'Question updated.')
            return redirect('lecturer:exam_detail', exam_id=exam.id)
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'lecturer/add_question.html', {
        'exam': exam,
        'question_form': question_form,
        'choice_formset': choice_formset,
        'editing': True,
        'question': question,
    })


@lecturer_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id, exam__created_by=request.user)
    exam = question.exam

    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted.')
        return redirect('lecturer:exam_detail', exam_id=exam.id)

    return render(request, 'lecturer/confirm_delete_question.html', {
        'question': question,
        'exam': exam,
    })


@lecturer_required
def exam_submissions(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    submissions = Submission.objects.filter(
        session__exam=exam
    ).select_related('session__student').order_by('-submitted_at')

    # summary stats
    stats = submissions.aggregate(
        avg_score=Avg('percentage'),
        total=Count('id'),
    )

    return render(request, 'lecturer/exam_submissions.html', {
        'exam': exam,
        'submissions': submissions,
        'stats': stats,
    })


@lecturer_required
def submission_detail(request, submission_id):
    submission = get_object_or_404(
        Submission,
        id=submission_id,
        session__exam__created_by=request.user
    )

    answers = submission.answers.select_related(
        'question', 'selected_choice'
    ).prefetch_related('question__choices').order_by('question__order')

    return render(request, 'lecturer/submission_detail.html', {
        'submission': submission,
        'answers': answers,
    })


@lecturer_required
def grade_submission(request, submission_id):
    """Manually grade short answer and essay questions."""
    submission = get_object_or_404(
        Submission,
        id=submission_id,
        session__exam__created_by=request.user
    )

    if request.method == 'POST':
        total_score = Decimal(submission.total_score)

        for answer in submission.answers.filter(
            question__question_type__in=['short', 'essay']
        ):
            field_key = f'marks_{answer.id}'

            if field_key in request.POST:
                try:
                    awarded = Decimal(request.POST[field_key])

                    # Prevent lecturer from awarding more than question marks
                    if awarded > answer.question.marks:
                        awarded = Decimal(answer.question.marks)

                    old = Decimal(answer.marks_awarded)

                    answer.marks_awarded = awarded
                    answer.save()

                    total_score += (awarded - old)

                except (ValueError, TypeError):
                    pass

        # Recalculate totals
        submission.total_score = total_score

        if submission.total_marks > 0:
            submission.percentage = round(
                (total_score / submission.total_marks) * Decimal('100'),
                2
            )
        else:
            submission.percentage = Decimal('0.00')

        from submissions.utils import calculate_grade
        submission.grade = calculate_grade(submission.percentage)

        submission.save()

        from notifications.utils import notify_result_released
        notify_result_released(submission)

        messages.success(request, 'Grades saved and student notified.')

        return redirect(
            'lecturer:submission_detail',
            submission_id=submission.id
        )

    return redirect(
        'lecturer:submission_detail',
        submission_id=submission.id
    )