from django.db.models import Avg, Count, Max, Min, Q
from submissions.models import Submission, Answer
from exams.models import Exam, Question
from proctoring.models import ProctoringLog

from django.db.models.functions import ExtractHour



def get_exam_stats(exam):
    """
    Returns a full statistical breakdown for a single exam.
    """

    submissions = Submission.objects.filter(session__exam=exam)

    if not submissions.exists():
        return None

    
    # ----OVERALL STATISTICS----
    
    aggregates = submissions.aggregate(
        avg_score=Avg('percentage'),
        highest_score=Max('percentage'),
        lowest_score=Min('percentage'),
        total_submissions=Count('id'),
    )

    # ---GRADE BREAKDOWN---

    grade_breakdown = submissions.values('grade').annotate(
        count=Count('id')
    ).order_by('grade')

    # ----PASS / FAIL----

    passed = submissions.exclude(grade='F').count()
    failed = submissions.filter(grade='F').count()

    total = aggregates['total_submissions'] or 0

    pass_rate = round((passed / total * 100), 1) if total > 0 else 0


    # ----QUESTION ANALYTICS----
    
    question_stats = []

    for question in exam.questions.all():
        q_answers = Answer.objects.filter(question=question)
        total_answers = q_answers.count()

        if question.question_type == 'mcq':
            correct = q_answers.filter(is_correct=True).count()
            correct_rate = (
                round((correct / total_answers * 100), 1)
                if total_answers > 0 else 0
            )
        else:
            correct = None
            correct_rate = None

        avg_marks = q_answers.aggregate(
            avg=Avg('marks_awarded')
        )['avg'] or 0

        question_stats.append({
            'question': question,
            'total_answers': total_answers,
            'correct': correct,
            'correct_rate': correct_rate,
            'avg_marks': round(float(avg_marks), 2),
            'difficulty': get_difficulty_label(correct_rate),
        })

    
    # ----TIMELINE (FIXED - NO .extra())----
    
    timeline = submissions.annotate(
        hour=ExtractHour('submitted_at')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')

    
    # ----PROCTORING SUMMARY----
    
    proctor_summary = ProctoringLog.objects.filter(
        session__exam=exam
    ).values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')

    
    # ----RETURN DATA----
    
    return {
        'aggregates': aggregates,
        'grade_breakdown': grade_breakdown,
        'passed': passed,
        'failed': failed,
        'pass_rate': pass_rate,
        'question_stats': question_stats,
        'timeline': timeline,
        'proctor_summary': proctor_summary,
    }


def get_lecturer_overview_stats(lecturer):
    """
    Returns aggregated stats across all exams created by a lecturer.
    """
    exams = Exam.objects.filter(created_by=lecturer)
    submissions = Submission.objects.filter(session__exam__created_by=lecturer)

    total_exams = exams.count()
    total_submissions = submissions.count()
    avg_score = submissions.aggregate(avg=Avg('percentage'))['avg'] or 0

    # per exam summary
    exam_summaries = []
    for exam in exams.order_by('-created_at')[:10]:
        exam_subs = submissions.filter(session__exam=exam)
        exam_summaries.append({
            'exam': exam,
            'submission_count': exam_subs.count(),
            'avg_score': round(exam_subs.aggregate(avg=Avg('percentage'))['avg'] or 0, 1),
            'pass_rate': round(
                exam_subs.exclude(grade='F').count() / exam_subs.count() * 100, 1
            ) if exam_subs.count() > 0 else 0,
        })

    # grade distribution across all exams
    grade_distribution = submissions.values('grade').annotate(
        count=Count('id')
    ).order_by('grade')

    return {
        'total_exams': total_exams,
        'total_submissions': total_submissions,
        'avg_score': round(avg_score, 1),
        'exam_summaries': exam_summaries,
        'grade_distribution': grade_distribution,
    }


def get_student_overview_stats(student):
    """
    Returns a student's personal performance stats across all exams.
    """
    submissions = Submission.objects.filter(
        session__student=student
    ).select_related('session__exam', 'session__exam__course')

    total_exams = submissions.count()
    avg_score = submissions.aggregate(avg=Avg('percentage'))['avg'] or 0
    highest = submissions.aggregate(h=Max('percentage'))['h'] or 0
    lowest = submissions.aggregate(l=Min('percentage'))['l'] or 0

    # performance per course
    course_stats = submissions.values(
        'session__exam__course__code',
        'session__exam__course__title',
    ).annotate(
        avg_score=Avg('percentage'),
        count=Count('id'),
    ).order_by('-avg_score')

    # grade breakdown
    grade_breakdown = submissions.values('grade').annotate(
        count=Count('id')
    ).order_by('grade')

    # recent performance trend (last 10 submissions)
    recent = submissions.order_by('-submitted_at')[:10]
    trend = [
        {
            'exam': sub.session.exam.title[:20],
            'score': float(sub.percentage),
            'grade': sub.grade,
        }
        for sub in reversed(list(recent))
    ]

    return {
        'total_exams': total_exams,
        'avg_score': round(avg_score, 1),
        'highest': highest,
        'lowest': lowest,
        'course_stats': course_stats,
        'grade_breakdown': grade_breakdown,
        'trend': trend,
    }


def get_admin_overview_stats():
    """
    Returns system-wide analytics for the admin portal.
    """
    from accounts.models import CustomUser
    from courses.models import Department, Course

    total_users = CustomUser.objects.count()
    total_students = CustomUser.objects.filter(role='student').count()
    total_lecturers = CustomUser.objects.filter(role='lecturer').count()
    total_exams = Exam.objects.count()
    total_submissions = Submission.objects.count()
    avg_score = Submission.objects.aggregate(avg=Avg('percentage'))['avg'] or 0

    # submissions per department
    dept_stats = Department.objects.annotate(
        submission_count=Count(
            'courses__exams__sessions__submission',
            distinct=True
        ),
        avg_score=Avg('courses__exams__sessions__submission__percentage'),
    ).order_by('-submission_count')

    # monthly submission trend
    monthly_trend = Submission.objects.extra(
        select={'month': "strftime('%%Y-%%m', submitted_at)"}
    ).values('month').annotate(
        count=Count('id'),
        avg_score=Avg('percentage'),
    ).order_by('month')

    # grade distribution
    grade_distribution = Submission.objects.values('grade').annotate(
        count=Count('id')
    ).order_by('grade')

    # top lecturers by avg student score
    top_lecturers = CustomUser.objects.filter(role='lecturer').annotate(
        avg_score=Avg('created_exams__sessions__submission__percentage'),
        submission_count=Count('created_exams__sessions__submission', distinct=True),
    ).filter(submission_count__gt=0).order_by('-avg_score')[:5]

    # proctoring overview
    total_alerts = ProctoringLog.objects.count()
    alert_breakdown = ProctoringLog.objects.values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')

    return {
        'total_users': total_users,
        'total_students': total_students,
        'total_lecturers': total_lecturers,
        'total_exams': total_exams,
        'total_submissions': total_submissions,
        'avg_score': round(avg_score, 1),
        'dept_stats': dept_stats,
        'monthly_trend': list(monthly_trend),
        'grade_distribution': grade_distribution,
        'top_lecturers': top_lecturers,
        'total_alerts': total_alerts,
        'alert_breakdown': alert_breakdown,
    }


def get_difficulty_label(correct_rate):
    if correct_rate is None:
        return None
    if correct_rate >= 75:
        return 'Easy'
    elif correct_rate >= 45:
        return 'Medium'
    else:
        return 'Hard'