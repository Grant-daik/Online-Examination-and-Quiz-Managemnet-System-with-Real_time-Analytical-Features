# Online Examination and AI-Based Invigilation System

## Overview

The Online Examination and AI-Based Invigilation System is a comprehensive web-based platform designed to facilitate secure, efficient, and scalable online examinations for educational institutions. The system enables administrators, lecturers, invigilators, and students to seamlessly manage the entire examination process while incorporating AI-assisted monitoring to help maintain examination integrity.

The application is built using Django and follows a modular architecture that separates major functionalities into dedicated applications for ease of maintenance, scalability, and future development.

---

## Features

### User Management

* Secure authentication and authorization
* Role-based access control
* Student, Lecturer, Invigilator, and Administrator accounts
* User profile management

### Course Management

* Create and manage courses
* Assign lecturers and students
* Organize examinations by course

### Examination Management

* Create examinations
* Schedule examinations
* Configure duration and instructions
* Automatic timing
* Multiple question support
* Randomized question ordering
* Automatic submission when time expires

### Student Portal

* View registered courses
* Access available examinations
* Take examinations online
* View examination history
* Track examination progress

### Lecturer Portal

* Create and manage examinations
* Manage questions
* View student submissions
* Review examination performance

### Invigilator Portal

* Monitor active examinations
* Track student activities
* Receive examination alerts
* View examination sessions in real time

### AI-Based Proctoring

* Real-time monitoring
* Suspicious activity detection
* Automated alert generation
* Examination session monitoring
* Violation logging

### Analytics Dashboard

* Examination statistics
* Student performance analysis
* Participation reports
* Examination activity summaries

### Notifications

* Examination reminders
* System notifications
* Real-time alerts

### Administrative Features

* User management
* Course administration
* Examination oversight
* System monitoring
* Dashboard reporting

---

## Technology Stack

### Backend

* Python
* Django
* Django REST Framework
* Django Channels
* Daphne
* Redis

### Database

* SQLite (Development)
* PostgreSQL (Production)

### Frontend

* HTML5
* CSS3
* Bootstrap
* JavaScript

### Deployment

* Gunicorn
* WhiteNoise
* Render (Recommended)
* PostgreSQL

---

## Project Structure

```text
accounts/
admin_portal/
analytics/
core/
courses/
exams/
invigilator_portal/
lecturer_portal/
notifications/
proctoring/
student_portal/
submissions/
templates/
static/
media/
exam_system/
manage.py
```

---

## Installation

Clone the repository

```bash
git clone <repository-url>
```

Navigate into the project

```bash
cd exam-system
```

Install dependencies

```bash
pip install -r requirements.txt
```


---

## Author

Erondu Chukwuebuka Grant

Data Scientist | Machine Learning Engineer | AI Developer | Full Stack Django Developer

---

## License

This project was developed for educational and research purposes.
