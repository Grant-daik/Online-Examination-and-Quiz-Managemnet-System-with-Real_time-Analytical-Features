# Create your models here.
from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f'{self.code} - {self.name}'


class Course(models.Model):
    SEMESTER_CHOICES = [
        ('first', 'First Semester'),
        ('second', 'Second Semester'),
    ]
    LEVEL_CHOICES = [(i, f'{i} Level') for i in range(100, 800, 100)]

    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    credit_units = models.PositiveIntegerField(default=2)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    level = models.IntegerField(choices=LEVEL_CHOICES)

    def __str__(self):
        return f'{self.code} - {self.title}'