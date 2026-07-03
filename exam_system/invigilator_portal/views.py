from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from exams.models import Exam, ExamSession
from proctoring.models import ProctoringLog, Snapshot
from submissions.utils import auto_submit_session
from notifications.utils import send_notification


def invigilator_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role not in ['invigilator', 'admin', 'lecturer']:
            messages.error(request, 'Access denied. Invigilators only.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


@invigilator_required
def dashboard(request):
    user = request.user
    now = timezone.now()

    # get assigned exams
    try:
        assigned_exams = user.invigilator_profile.assigned_exams.all()
    except Exception:
        assigned_exams = Exam.objects.none()

    active_exams = assigned_exams.filter(
        status='published',
        start_time__lte=now,
        end_time__gte=now,
    )

    upcoming_exams = assigned_exams.filter(
        status='published',
        start_time__gt=now,
    ).order_by('start_time')[:5]

    # recent suspicious events across all assigned exams
    recent_alerts = ProctoringLog.objects.filter(
        session__exam__in=assigned_exams,
    ).select_related(
        'session__student',
        'session__exam',
    ).order_by('-timestamp')[:10]

    return render(request, 'invigilator/dashboard.html', {
        'active_exams': active_exams,
        'upcoming_exams': upcoming_exams,
        'recent_alerts': recent_alerts,
    })


@invigilator_required
def assigned_exams(request):
    user = request.user
    now = timezone.now()

    try:
        exams = user.invigilator_profile.assigned_exams.all().order_by('start_time')
    except Exception:
        exams = Exam.objects.none()

    for exam in exams:
        exam.active_sessions = ExamSession.objects.filter(
            exam=exam,
            is_submitted=False,
        ).count()
        exam.total_sessions = ExamSession.objects.filter(exam=exam).count()

    return render(request, 'invigilator/assigned_exams.html', {
        'exams': exams,
        'now': now,
    })


@invigilator_required
def monitor_exam(request, exam_id):
    """
    Live monitoring dashboard for a single exam.
    Shows all active student sessions and their proctoring status in real time.
    The page connects to the MonitorConsumer WebSocket to receive live alerts.
    """
    try:
        exam = get_object_or_404(
            request.user.invigilator_profile.assigned_exams,
            id=exam_id,
        )
    except Exception:
        messages.error(request, 'You are not assigned to this exam.')
        return redirect('invigilator:assigned_exams')

    active_sessions = ExamSession.objects.filter(
        exam=exam,
        is_submitted=False,
    ).select_related('student').prefetch_related('proctoring_logs')

    # attach alert count and last event to each session
    for session in active_sessions:
        session.alert_count = session.proctoring_logs.count()
        session.last_alert = session.proctoring_logs.first()

    return render(request, 'invigilator/monitor_exam.html', {
        'exam': exam,
        'active_sessions': active_sessions,
    })


@invigilator_required
def exam_sessions(request, exam_id):
    """Full list of all sessions (active and submitted) for an exam."""
    try:
        exam = get_object_or_404(
            request.user.invigilator_profile.assigned_exams,
            id=exam_id,
        )
    except Exception:
        messages.error(request, 'You are not assigned to this exam.')
        return redirect('invigilator:assigned_exams')

    sessions = ExamSession.objects.filter(
        exam=exam,
    ).select_related('student').order_by('started_at')

    for session in sessions:
        session.alert_count = session.proctoring_logs.count()

    return render(request, 'invigilator/exam_sessions.html', {
        'exam': exam,
        'sessions': sessions,
    })


@invigilator_required
def session_logs(request, session_id):
    """View all proctoring logs for a specific student session."""
    session = get_object_or_404(ExamSession, id=session_id)

    logs = ProctoringLog.objects.filter(
        session=session,
    ).order_by('-timestamp')

    return render(request, 'invigilator/session_logs.html', {
        'session': session,
        'logs': logs,
    })


@invigilator_required
def session_snapshots(request, session_id):
    """View all webcam snapshots captured during a student session."""
    session = get_object_or_404(ExamSession, id=session_id)

    snapshots = Snapshot.objects.filter(
        session=session,
    ).order_by('-captured_at')

    return render(request, 'invigilator/session_snapshots.html', {
        'session': session,
        'snapshots': snapshots,
    })


@invigilator_required
def flag_session(request, session_id):
    """Flag a student session as suspicious."""
    session = get_object_or_404(ExamSession, id=session_id)

    if request.method == 'POST':
        reason = request.POST.get('reason', 'Flagged by invigilator')

        ProctoringLog.objects.create(
            session=session,
            event_type='suspicious_movement',
            details={'reason': reason, 'flagged_by': request.user.get_full_name()},
        )

        send_notification(
            recipient=session.exam.created_by,
            title=f'Session flagged — {session.student.get_full_name()}',
            message=f'{request.user.get_full_name()} flagged {session.student.get_full_name()} during {session.exam.title}. Reason: {reason}',
            notif_type='proctor_alert',
        )

        messages.success(request, f'Session flagged and lecturer notified.')
        return redirect('invigilator:session_logs', session_id=session.id)

    return render(request, 'invigilator/flag_session.html', {'session': session})


@invigilator_required
def terminate_session(request, session_id):
    """Force submit a student session."""
    session = get_object_or_404(ExamSession, id=session_id)

    if session.is_submitted:
        messages.info(request, 'This session has already been submitted.')
        return redirect('invigilator:exam_sessions', exam_id=session.exam.id)

    if request.method == 'POST':
        submission = auto_submit_session(session)

        send_notification(
            recipient=session.student,
            title=f'Exam terminated — {session.exam.title}',
            message=f'Your exam session was terminated by an invigilator.',
            notif_type='general',
        )

        send_notification(
            recipient=session.exam.created_by,
            title=f'Session terminated — {session.student.get_full_name()}',
            message=f'{request.user.get_full_name()} terminated {session.student.get_full_name()}\'s session during {session.exam.title}.',
            notif_type='proctor_alert',
        )

        messages.success(request, f'{session.student.get_full_name()}\'s session has been terminated and auto-submitted.')
        return redirect('invigilator:exam_sessions', exam_id=session.exam.id)

    return render(request, 'invigilator/terminate_session.html', {'session': session})