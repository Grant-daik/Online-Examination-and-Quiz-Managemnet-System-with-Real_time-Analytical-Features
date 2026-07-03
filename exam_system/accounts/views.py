from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, RegisterForm, StudentProfileForm, LecturerProfileForm, InvigilatorProfileForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect_by_role(user)
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    form = RegisterForm(request.POST or None)
    profile_form = None

    if request.method == 'POST':
        role = request.POST.get('role')
        profile_form = get_profile_form(role, request.POST)

        if form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user = form.save()

            if profile_form:
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
                if hasattr(profile_form, 'save_m2m'):
                    profile_form.save_m2m()

            login(request, user)
            messages.success(request, f'Account created successfully. Welcome, {user.first_name}!')
            return redirect_by_role(user)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        role = request.GET.get('role', 'student')
        profile_form = get_profile_form(role)

    return render(request, 'accounts/register.html', {
        'form': form,
        'profile_form': profile_form,
    })


@login_required
def profile_view(request):
    user = request.user
    profile_form = None
    profile = get_user_profile(user)
    ProfileFormClass = get_profile_form_class(user.role)

    if request.method == 'POST':
        if ProfileFormClass and profile:
            profile_form = ProfileFormClass(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('accounts:profile')
        else:
            messages.error(request, 'Could not update profile.')
    else:
        if ProfileFormClass and profile:
            profile_form = ProfileFormClass(instance=profile)

    return render(request, 'accounts/profile.html', {
        'profile_form': profile_form,
        'profile': profile,
    })


# --- helpers ---

def redirect_by_role(user):
    role_redirects = {
        'admin': '/admin/',
        'lecturer': '/lecturer/dashboard/',
        'student': '/student/dashboard/',
        'invigilator': '/invigilator/dashboard/',
    }
    return redirect(role_redirects.get(user.role, '/'))


def get_profile_form(role, data=None):
    forms_map = {
        'student': StudentProfileForm,
        'lecturer': LecturerProfileForm,
        'invigilator': InvigilatorProfileForm,
    }
    FormClass = forms_map.get(role)
    return FormClass(data) if FormClass else None


def get_profile_form_class(role):
    from .forms import StudentProfileForm, LecturerProfileForm, InvigilatorProfileForm
    return {
        'student': StudentProfileForm,
        'lecturer': LecturerProfileForm,
        'invigilator': InvigilatorProfileForm,
    }.get(role)


def get_user_profile(user):
    try:
        if user.role == 'student':
            return user.student_profile
        elif user.role == 'lecturer':
            return user.lecturer_profile
        elif user.role == 'invigilator':
            return user.invigilator_profile
    except Exception:
        return None