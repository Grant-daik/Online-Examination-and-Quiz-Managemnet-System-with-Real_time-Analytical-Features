from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg, Q
from accounts.models import CustomUser, StudentProfile, LecturerProfile, InvigilatorProfile
from courses.models import Department, Course
from exams.models import Exam, ExamSession
from submissions.models import Submission
from proctoring.models import ProctoringLog
from .forms import DepartmentForm, CourseForm, AssignInvigilatorForm


def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'admin':
            messages.error(request, 'Access denied. Admins only.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return wrapper


# --- dashboard ---

@admin_required
def dashboard(request):
    total_users = CustomUser.objects.count()
    total_students = CustomUser.objects.filter(role='student').count()
    total_lecturers = CustomUser.objects.filter(role='lecturer').count()
    total_exams = Exam.objects.count()
    total_submissions = Submission.objects.count()
    total_departments = Department.objects.count()
    total_courses = Course.objects.count()

    now = timezone.now()
    active_exams = Exam.objects.filter(
        status='published',
        start_time__lte=now,
        end_time__gte=now,
    ).count()

    recent_users = CustomUser.objects.order_by('-date_joined')[:5]
    recent_exams = Exam.objects.order_by('-created_at')[:5]
    recent_submissions = Submission.objects.select_related(
        'session__student', 'session__exam'
    ).order_by('-submitted_at')[:5]

    return render(request, 'admin_portal/dashboard.html', {
        'total_users': total_users,
        'total_students': total_students,
        'total_lecturers': total_lecturers,
        'total_exams': total_exams,
        'total_submissions': total_submissions,
        'total_departments': total_departments,
        'total_courses': total_courses,
        'active_exams': active_exams,
        'recent_users': recent_users,
        'recent_exams': recent_exams,
        'recent_submissions': recent_submissions,
    })


# --- user management ---

@admin_required
def user_list(request):
    role_filter = request.GET.get('role', '')
    search = request.GET.get('search', '')

    users = CustomUser.objects.all().order_by('-date_joined')

    if role_filter:
        users = users.filter(role=role_filter)

    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    return render(request, 'admin_portal/user_list.html', {
        'users': users,
        'role_filter': role_filter,
        'search': search,
    })



@admin_required
def user_detail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    profile = None
    if user.role == 'student':
        profile = getattr(user, 'student_profile', None)
    elif user.role == 'lecturer':
        profile = getattr(user, 'lecturer_profile', None)
    elif user.role == 'invigilator':
        profile = getattr(user, 'invigilator_profile', None)

    submissions = None
    if user.role == 'student':
        submissions = Submission.objects.filter(
            session__student=user
        ).select_related('session__exam').order_by('-submitted_at')[:10]

    exams = None
    if user.role == 'lecturer':
        exams = Exam.objects.filter(created_by=user).order_by('-created_at')[:10]

    return render(request, 'admin_portal/user_detail.html', {
        'viewed_user': user,
        'profile': profile,
        'submissions': submissions,
        'exams': exams,
    })


@admin_required
def toggle_user_active(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'{user.get_full_name()} has been {status}.')
        return redirect('admin_portal:user_detail', user_id=user.id)

    return redirect('admin_portal:user_list')


@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('admin_portal:user_list')

    if request.method == 'POST':
        name = user.get_full_name()
        user.delete()
        messages.success(request, f'{name} has been deleted.')
        return redirect('admin_portal:user_list')

    return render(request, 'admin_portal/confirm_delete.html', {
        'object_name': user.get_full_name(),
        'cancel_url': 'admin_portal:user_list',
    })


# --- department management ---

@admin_required
def department_list(request):
    departments = Department.objects.annotate(
        course_count=Count('courses')
    ).order_by('name')

    return render(request, 'admin_portal/department_list.html', {
        'departments': departments,
    })


@admin_required
def create_department(request):
    form = DepartmentForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Department created.')
            return redirect('admin_portal:department_list')

    return render(request, 'admin_portal/department_form.html', {
        'form': form,
        'title': 'Create department',
    })


@admin_required
def edit_department(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    form = DepartmentForm(request.POST or None, instance=department)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated.')
            return redirect('admin_portal:department_list')

    return render(request, 'admin_portal/department_form.html', {
        'form': form,
        'title': 'Edit department',
        'editing': True,
    })


@admin_required
def delete_department(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)

    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted.')
        return redirect('admin_portal:department_list')

    return render(request, 'admin_portal/confirm_delete.html', {
        'object_name': department.name,
        'cancel_url': 'admin_portal:department_list',
    })


# --- course management ---

@admin_required
def course_list(request):
    dept_filter = request.GET.get('department', '')
    courses = Course.objects.select_related('department').order_by('department', 'code')

    if dept_filter:
        courses = courses.filter(department_id=dept_filter)

    departments = Department.objects.all()

    return render(request, 'admin_portal/course_list.html', {
        'courses': courses,
        'departments': departments,
        'dept_filter': dept_filter,
    })


@admin_required
def create_course(request):
    form = CourseForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Course created.')
            return redirect('admin_portal:course_list')

    return render(request, 'admin_portal/course_form.html', {
        'form': form,
        'title': 'Create course',
    })


@admin_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, instance=course)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated.')
            return redirect('admin_portal:course_list')

    return render(request, 'admin_portal/course_form.html', {
        'form': form,
        'title': 'Edit course',
        'editing': True,
    })


@admin_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted.')
        return redirect('admin_portal:course_list')

    return render(request, 'admin_portal/confirm_delete.html', {
        'object_name': f'{course.code} — {course.title}',
        'cancel_url': 'admin_portal:course_list',
    })


# --- exam oversight ---

@admin_required
def exam_oversight(request):
    status_filter = request.GET.get('status', '')
    exams = Exam.objects.select_related(
        'course', 'created_by'
    ).order_by('-created_at')

    if status_filter:
        exams = exams.filter(status=status_filter)

    for exam in exams:
        exam.submission_count = Submission.objects.filter(session__exam=exam).count()

    return render(request, 'admin_portal/exam_oversight.html', {
        'exams': exams,
        'status_filter': status_filter,
    })


@admin_required
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == 'POST':
        title = exam.title
        exam.delete()
        messages.success(request, f'Exam "{title}" deleted.')
        return redirect('admin_portal:exam_oversight')

    return render(request, 'admin_portal/confirm_delete.html', {
        'object_name': exam.title,
        'cancel_url': 'admin_portal:exam_oversight',
    })



@admin_required
def assign_invigilator(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    current_invigilators = CustomUser.objects.filter(
        role='invigilator',
        invigilator_profile__assigned_exams=exam, 
    )

    form = AssignInvigilatorForm(
        request.POST or None,
        initial={'invigilators': current_invigilators},
    )

    if request.method == 'POST':
        if form.is_valid():
            selected_users = form.cleaned_data['invigilators']

            for invigilator_profile in InvigilatorProfile.objects.all():
                if invigilator_profile.user in selected_users:
                    exam.invigilators.add(invigilator_profile)      
                else:
                    exam.invigilators.remove(invigilator_profile)   

            messages.success(request, f'Invigilators assigned to "{exam.title}".')
            return redirect('admin_portal:exam_oversight')

    return render(request, 'admin_portal/assign_invigilator.html', {
        'exam': exam,
        'form': form,
        'current_invigilators': current_invigilators,
    })



# --- analytics ---

@admin_required
def analytics(request):
    # overall stats
    total_submissions = Submission.objects.count()
    avg_score = Submission.objects.aggregate(avg=Avg('percentage'))['avg'] or 0

    # grade distribution
    grade_distribution = Submission.objects.values('grade').annotate(
        count=Count('id')
    ).order_by('grade')

    # top performing exams
    top_exams = Exam.objects.annotate(
        avg_score=Avg('sessions__submission__percentage'),
        submission_count=Count('sessions__submission'),
    ).filter(submission_count__gt=0).order_by('-avg_score')[:5]

    # submissions per department
    dept_stats = Department.objects.annotate(
        submission_count=Count('courses__exams__sessions__submission'),
    ).order_by('-submission_count')

    # recent proctoring events summary
    alert_summary = ProctoringLog.objects.values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')

    return render(request, 'admin_portal/analytics.html', {
        'total_submissions': total_submissions,
        'avg_score': round(avg_score, 2),
        'grade_distribution': grade_distribution,
        'top_exams': top_exams,
        'dept_stats': dept_stats,
        'alert_summary': alert_summary,
    })