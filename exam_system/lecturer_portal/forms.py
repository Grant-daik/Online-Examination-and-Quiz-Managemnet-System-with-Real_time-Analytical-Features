from django import forms
from exams.models import Exam, Question, Choice


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'title', 'course', 'duration_minutes',
            'start_time', 'end_time', 'instructions',
            'shuffle_questions', 'shuffle_choices',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Exam title'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Instructions for students...'}),
            'shuffle_questions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'shuffle_choices': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and end <= start:
            raise forms.ValidationError('End time must be after start time.')
        return cleaned_data


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'marks', 'order', 'image']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Question text'}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choice text'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# formset for adding multiple choices to a question at once
ChoiceFormSet = forms.inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    extra=4,
    max_num=6,
    can_delete=True,
)


class ManualGradeForm(forms.Form):
    """Used by lecturers to manually grade short answer and essay questions."""
    marks_awarded = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.5'})
    )
    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional feedback...'})
    )