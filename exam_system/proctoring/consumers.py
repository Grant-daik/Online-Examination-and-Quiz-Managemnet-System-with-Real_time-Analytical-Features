import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ProctoringConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket connections for a student's exam session.
    - Receives proctoring events from the student's browser
    - Forwards alerts to the invigilator/lecturer monitoring dashboard
    - Handles timer sync
    """

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.exam_group = f'exam_{self.session_id}'
        self.user = self.scope['user']

        # reject unauthenticated connections
        if not self.user.is_authenticated:
            await self.close()
            return

        # join the exam group
        await self.channel_layer.group_add(
            self.exam_group,
            self.channel_name
        )

        await self.accept()

        # send current time remaining on connect/reconnect
        time_remaining = await self.get_time_remaining()
        await self.send(text_data=json.dumps({
            'type': 'timer_sync',
            'time_remaining': time_remaining,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.exam_group,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'proctor_event':
            await self.handle_proctor_event(data)

        elif message_type == 'timer_sync':
            await self.handle_timer_sync(data)

        elif message_type == 'save_answer':
            await self.handle_save_answer(data)

    async def handle_proctor_event(self, data):
        event_type = data.get('event_type')
        details = data.get('details', {})

        # save to database
        await self.log_event(event_type, details)

        # forward alert to invigilator monitoring group
        await self.channel_layer.group_send(
            f'monitor_{self.session_id}',
            {
                'type': 'proctor_alert',
                'event_type': event_type,
                'student': self.user.get_full_name(),
                'session_id': self.session_id,
                'timestamp': timezone.now().isoformat(),
                'details': details,
            }
        )

    async def handle_timer_sync(self, data):
        time_remaining = await self.update_time_remaining(data.get('time_remaining'))
        await self.send(text_data=json.dumps({
            'type': 'timer_sync',
            'time_remaining': time_remaining,
        }))

    async def handle_save_answer(self, data):
        saved = await self.save_answer(
            question_id=data.get('question_id'),
            choice_id=data.get('choice_id'),
            text_answer=data.get('text_answer', ''),
        )
        await self.send(text_data=json.dumps({
            'type': 'answer_saved',
            'question_id': data.get('question_id'),
            'status': 'ok' if saved else 'error',
        }))

    async def proctor_alert(self, event):
        await self.send(text_data=json.dumps(event))

    async def exam_closed(self, event):
        await self.send(text_data=json.dumps({
            'type': 'exam_closed',
            'message': event.get('message', 'Exam has been closed.'),
        }))

    # --- database helpers ---

    @database_sync_to_async
    def get_time_remaining(self):
        from exams.models import ExamSession
        try:
            session = ExamSession.objects.get(id=self.session_id)
            return session.time_remaining
        except ExamSession.DoesNotExist:
            return None

    @database_sync_to_async
    def update_time_remaining(self, time_remaining):
        from exams.models import ExamSession
        try:
            session = ExamSession.objects.get(id=self.session_id)
            session.time_remaining = time_remaining
            session.save(update_fields=['time_remaining'])
            return time_remaining
        except ExamSession.DoesNotExist:
            return None

    @database_sync_to_async
    def log_event(self, event_type, details):
        from exams.models import ExamSession
        from .models import ProctoringLog
        try:
            session = ExamSession.objects.get(id=self.session_id)
            ProctoringLog.objects.create(
                session=session,
                event_type=event_type,
                details=details,
            )
        except ExamSession.DoesNotExist:
            pass

    @database_sync_to_async
    def save_answer(self, question_id, choice_id, text_answer):
        from exams.models import ExamSession, Question, Choice
        from submissions.models import SavedAnswer
        try:
            session = ExamSession.objects.get(id=self.session_id)
            question = Question.objects.get(id=question_id)
            choice = Choice.objects.get(id=choice_id) if choice_id else None

            SavedAnswer.objects.update_or_create(
                session=session,
                question=question,
                defaults={
                    'selected_choice': choice,
                    'text_answer': text_answer,
                }
            )
            return True
        except Exception:
            return False


class MonitorConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket connections for the invigilator/lecturer
    monitoring dashboard. Receives alerts forwarded from ProctoringConsumer.
    """

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.monitor_group = f'monitor_{self.session_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.monitor_group,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.monitor_group,
            self.channel_name
        )

    async def proctor_alert(self, event):
        await self.send(text_data=json.dumps(event))