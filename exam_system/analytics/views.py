import csv
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from exams.models import Exam
from submissions.models import Submission
from .utils import (
    get_exam_stats,
    get_lecturer_overview_stats,
    get_student_overview_stats,
    get_admin_overview_stats,
)

from decimal import Decimal

def convert_decimals(obj):
    """
    Recursively convert Decimal values to float for JSON serialization.
    """
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]

    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}

    if isinstance(obj, Decimal):
        return float(obj)

    return obj


def role_required(*roles):
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, 'Access denied.')
                return redirect('accounts:login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@role_required('lecturer', 'admin')
def exam_analytics(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    # lecturers can only view their own exams
    if request.user.role == 'lecturer' and exam.created_by != request.user:
        messages.error(request, 'Access denied.')
        return redirect('lecturer:exam_list')

    stats = get_exam_stats(exam)

    # prepare chart data as JSON for Chart.js
    chart_data = {}
    if stats:
        chart_data = {
            'grades': {
                'labels': [item['grade'] for item in stats['grade_breakdown']],
                'data': [item['count'] for item in stats['grade_breakdown']],
            },
            'questions': {
                'labels': [f'Q{i+1}' for i, _ in enumerate(stats['question_stats'])],
                'correct_rates': [
                    q['correct_rate'] or 0
                    for q in stats['question_stats']
                ],
                'avg_marks': [
                    float(q['avg_marks'])
                    for q in stats['question_stats']
                ],
            },

            
            'timeline': {
                'labels': [f"{item['hour']}:00" for item in stats['timeline']],
                'data': [item['count'] for item in stats['timeline']],
            },
        }

    return render(request, 'analytics/exam_analytics.html', {
        'exam': exam,
        'stats': stats,
        'chart_data': json.dumps(chart_data),
    })


@role_required('lecturer')
def lecturer_overview(request):
    stats = get_lecturer_overview_stats(request.user)

    chart_data = {
        'grades': {
            'labels': [item['grade'] for item in stats['grade_distribution']],
            'data': [float(item['count']) for item in stats['grade_distribution']],
        },
        'exams': {
            'labels': [s['exam'].title[:15] for s in stats['exam_summaries']],
            'avg_scores': [float(s['avg_score']) for s in stats['exam_summaries']],
            'pass_rates': [float(s['pass_rate']) for s in stats['exam_summaries']],
        },
    }

    return render(request, 'analytics/lecturer_overview.html', {
        'stats': stats,
        'chart_data': json.dumps(convert_decimals(chart_data)),
    })


@role_required('student')
def student_overview(request):
    stats = get_student_overview_stats(request.user)

    chart_data = {
        'trend': {
            'labels': [t['exam'] for t in stats['trend']],
            'scores': [t['score'] for t in stats['trend']],
        },
        'grades': {
            'labels': [item['grade'] for item in stats['grade_breakdown']],
            'data': [item['count'] for item in stats['grade_breakdown']],
        },
    }

    return render(request, 'analytics/student_overview.html', {
        'stats': stats,
        'chart_data': json.dumps(chart_data),
    })


@role_required('admin')
def admin_overview(request):
    stats = get_admin_overview_stats()

    chart_data = {
        'grades': {
            'labels': [item['grade'] for item in stats['grade_distribution']],
            'data': [item['count'] for item in stats['grade_distribution']],
        },
        'monthly': {
            'labels': [item['month'] for item in stats['monthly_trend']],
            'data': [item['count'] for item in stats['monthly_trend']],
            'avg_scores': [
                round(item['avg_score'] or 0, 1)
                for item in stats['monthly_trend']
            ],
        },
    }

    return render(request, 'analytics/admin_overview.html', {
        'stats': stats,
        'chart_data': json.dumps(convert_decimals(chart_data)),
    })


@role_required('lecturer', 'admin')
def export_exam_csv(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.user.role == 'lecturer' and exam.created_by != request.user:
        messages.error(request, 'Access denied.')
        return redirect('lecturer:exam_list')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{exam.title}_results.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Student name', 'Email', 'Matric number',
        'Score', 'Total marks', 'Percentage', 'Grade',
        'Submitted at', 'Auto submitted',
    ])

    submissions = Submission.objects.filter(
        session__exam=exam
    ).select_related('session__student').order_by('-submitted_at')

    for sub in submissions:
        student = sub.session.student
        matric = ''
        try:
            matric = student.student_profile.matric_number
        except Exception:
            pass

        writer.writerow([
            student.get_full_name(),
            student.email,
            matric,
            sub.total_score,
            sub.total_marks,
            sub.percentage,
            sub.grade,
            sub.submitted_at.strftime('%Y-%m-%d %H:%M'),
            'Yes' if sub.session.is_auto_submitted else 'No',
        ])

    return response


@role_required('lecturer', 'admin')
def export_exam_pdf(request, exam_id):
    """
    Basic PDF export using HTML-to-PDF approach.
    Install weasyprint: pip install weasyprint
    """
    exam = get_object_or_404(Exam, id=exam_id)

    if request.user.role == 'lecturer' and exam.created_by != request.user:
        messages.error(request, 'Access denied.')
        return redirect('lecturer:exam_list')

    submissions = Submission.objects.filter(
        session__exam=exam
    ).select_related('session__student').order_by('-submitted_at')

    stats = get_exam_stats(exam)

    try:
        from weasyprint import HTML
        from django.template.loader import render_to_string

        html_string = render_to_string('analytics/exam_report_pdf.html', {
            'exam': exam,
            'submissions': submissions,
            'stats': stats,
        })

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{exam.title}_report.pdf"'
        HTML(string=html_string).write_pdf(response)
        return response

    except ImportError:
        messages.error(request, 'PDF export requires weasyprint. Install it with: pip install weasyprint')
        return redirect('analytics:exam_analytics', exam_id=exam.id)