import random
from .models import Question, Choice


def get_shuffled_questions(exam):
    questions = list(exam.questions.all())
    if exam.shuffle_questions:
        random.shuffle(questions)
    return questions


def get_shuffled_choices(question):
    choices = list(question.choices.all())
    if question.exam.shuffle_choices:
        random.shuffle(choices)
    return choices


def calculate_total_marks(exam):
    return sum(q.marks for q in exam.questions.all())