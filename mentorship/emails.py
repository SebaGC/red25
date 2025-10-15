from django.conf import settings
from django.core.mail import send_mail


def send_session_note_notification(session):
    subject = f"New session notes for Dupla #{session.dupla_id}"
    message = (
        f"A new update was posted for the session on {session.date}.\n"
        "Mentor notes present: {mentor_notes}\n"
        "Mentee notes present: {mentee_notes}\n"
    ).format(
        mentor_notes=bool(session.notes_by_mentor),
        mentee_notes=bool(session.notes_by_mentee),
    )

    recipients = [
        session.dupla.mentor.email,
        session.dupla.mentee.email,
    ]

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=True,
    )
