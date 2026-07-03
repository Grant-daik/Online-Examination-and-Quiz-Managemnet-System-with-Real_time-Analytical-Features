from django import forms
from accounts.models import CustomUser, InvigilatorProfile
from courses.models import Department, Course
from exams.models import Exam


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CSC'}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'code', 'department', 'credit_units', 'semester', 'level']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course title'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CSC301'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'credit_units': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }


class AssignInvigilatorForm(forms.Form):
    invigilators = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role='invigilator'),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Assign invigilators',
    )

