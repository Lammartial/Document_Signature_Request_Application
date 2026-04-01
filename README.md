# Document_Signature_Request_Application

Python-first replacement for the current Power Apps + Power Automate document signature request app.

## What exists now

The initial Django codebase is scaffolded with:

- authentication and admin
- request creation with file upload
- ordered approver chain
- sequential approve/reject workflow
- requester cancellation
- audit logging
- email notification hooks
- Celery/Redis wiring for background jobs

## Stack

- Django
- Celery
- Redis
- SQLite for local development
- PostgreSQL later for production
- Bootstrap templates for the first UI pass

## Local setup

Python 3.11+ is required. This workspace does not currently have Python installed, so the app has not been executed yet.

### Option 1: local Python

1. Create a virtual environment.
2. Install the package with `pip install -e .`
3. Copy `.env.example` to `.env`
4. Run `python manage.py migrate`
5. Run `python manage.py createsuperuser`
6. Run `python manage.py runserver`

### Option 2: Docker Compose

1. Run `docker compose up --build`
2. Open `http://localhost:8000`

## Next implementation steps

- add PDF conversion and stamping
- capture handwritten signature data in the browser
- add reminder and timeout jobs
- switch local SQLite assumptions to PostgreSQL-ready settings
- improve the UI to match the existing approval screens more closely
