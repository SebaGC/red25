# red25

Plataforma Red de Mentores 2025

## Backend Overview

This repository includes a Django REST backend for tracking mentorship programs. Key features:

- Custom user model with Mentor, Mentee, and Admin roles.
- Program management with mentor/mentee assignments and duet (Dupla) tracking.
- Session minute upload endpoints with email notification stubs.
- Role-based permissions for core flows: registration, program creation, matching, and session management.
- Hooks for integrating OpenAI-powered summaries and future dashboards or messaging modules.

### Getting Started

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Apply migrations and create a superuser:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. Run the development server:

   ```bash
   python manage.py runserver
   ```

### Environment Variables

- `DJANGO_SECRET_KEY`: Secret key for Django.
- `OPENAI_API_KEY`: Required to enable AI-powered session summaries.

### Running Tests

Add automated tests inside the `mentorship` app and run them via `python manage.py test`.
