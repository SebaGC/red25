import logging

try:
    import openai
except ImportError:  # pragma: no cover - optional dependency
    openai = None

logger = logging.getLogger(__name__)


def generate_ai_session_summary(session):
    if not openai:
        return 'OpenAI SDK is not installed. Please install openai to enable AI summaries.'

    prompt = (
        "Summarize the following mentorship session notes in under 150 words.\n\n"
        f"Mentor notes: {session.notes_by_mentor}\n\n"
        f"Mentee notes: {session.notes_by_mentee}"
    )
    try:
        response = openai.ChatCompletion.create(
            model='gpt-4o-mini',
            messages=[{'role': 'system', 'content': 'You are a concise mentorship program assistant.'},
                      {'role': 'user', 'content': prompt}],
        )
    except Exception as exc:  # pragma: no cover - external API failure
        logger.exception('Failed to generate AI summary: %s', exc)
        return 'AI summary could not be generated at this time.'

    return response['choices'][0]['message']['content']
