# Online Exam and Quiz Management System with Real-time Anatyitcs Features Structure,

6 Django apps, each with a clear responsibility — accounts handles who you are, exams handles what the exam contains, submissions handles what students answer, proctoring handles live monitoring, analytics handles reporting, and notifications handles alerts. Keeping them separate means you can work on one without touching the others.

consumers.py in proctoring — this is where all the WebSocket logic lives. Django Channels routes WebSocket connections here instead of to regular Django views.

# Database schema (Model Structure)

courses is its own app — I added it separately from exams because Department and Course are shared across multiple apps (accounts, exams, analytics). Keeping them in their own app avoids circular imports.

CustomUser has a role field — rather than creating four separate user models, one user model with a role field is cleaner. Each role then gets its own profile model with extra fields specific to that role.

ExamSession is the central link — it connects a student to an exam attempt. Everything else (answers, proctoring logs, snapshots) hangs off it. This makes it easy to track every student's individual exam experience.

time_remaining on ExamSession — this is stored server-side so if a student loses connection and reconnects, the correct time is restored from the database, not the browser.

pip install gunicorn daphne psycopg2-binary django-environ whitenoise