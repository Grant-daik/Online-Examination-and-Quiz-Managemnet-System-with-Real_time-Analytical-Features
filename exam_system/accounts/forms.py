from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser, StudentProfile, LecturerProfile, InvigilatorProfile
from courses.models import Department, Course


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
        })
    )


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'role']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['matric_number', 'department', 'level', 'enrolled_courses']
        widgets = {
            'matric_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matric number'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'enrolled_courses': forms.CheckboxSelectMultiple(),
        }


class LecturerProfileForm(forms.ModelForm):
    class Meta:
        model = LecturerProfile
        fields = ['staff_id', 'department', 'courses']
        widgets = {
            'staff_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Staff ID'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'courses': forms.CheckboxSelectMultiple(),
        }


class InvigilatorProfileForm(forms.ModelForm):
    class Meta:
        model = InvigilatorProfile
        fields = ['staff_id', 'department']
        widgets = {
            'staff_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Staff ID'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }