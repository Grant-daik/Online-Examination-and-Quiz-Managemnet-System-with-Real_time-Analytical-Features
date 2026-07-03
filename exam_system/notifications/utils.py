from .models import Notification


def send_notification(recipient, title, message, notif_type='general'):
    """
    Creates an in-app notification for a single user.
    """
    return Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notif_type=notif_type,
    )


def send_bulk_notification(recipients, title, message, notif_type='general'):
    """
    Creates notifications for multiple users at once efficiently.
    Used for exam reminders, result releases, etc.
    """
    notifications = [
        Notification(
            recipient=user,
            title=title,
            message=message,
            notif_type=notif_type,
        )
        for user in recipients
    ]
    Notification.objects.bulk_create(notifications)


def notify_exam_published(exam):
    """
    Notifies all students enrolled in the course when an exam is published.
    """
    enrolled_students = exam.course.enrolled_students.all()
    send_bulk_notification(
        recipients=[s.user for s in enrolled_students],
        title=f'New exam: {exam.title}',
        message=f'A new exam for {exam.course.title} has been published. It starts on {exam.start_time.strftime("%d %b %Y at %H:%M")}.',
        notif_type='exam_published',
    )


def notify_result_released(submission):
    """
    Notifies a student when their result is available.
    """
    student = submission.session.student
    exam = submission.session.exam
    send_notification(
        recipient=student,
        title=f'Result available: {exam.title}',
        message=f'Your result for {exam.title} is ready. You scored {submission.percentage}% — Grade {submission.grade}.',
        notif_type='result_released',
    )


def notify_proctor_alert(session, event_type):
    """
    Notifies the exam creator and assigned invigilators about a suspicious event.
    """
    exam = session.exam
    student_name = session.student.get_full_name()

    recipients = [exam.created_by]

    # also notify assigned invigilators
    invigilators = exam.invigilatorprofile_set.select_related('user').all()
    for inv in invigilators:
        recipients.append(inv.user)

    for recipient in recipients:
        send_notification(
            recipient=recipient,
            title=f'Proctoring alert — {student_name}',
            message=f'{student_name} triggered a {event_type.replace("_", " ")} event during {exam.title}.',
            notif_type='proctor_alert',
        )