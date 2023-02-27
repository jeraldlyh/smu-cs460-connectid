from database.models import Responder
from telebot.formatting import hbold, hitalic


def format_form_text(responder: Responder, content: str) -> str:
    body = f"<b><u>Onboarding Form | Step {responder.state.value}</u></b>"
    body += "\n\n"
    body += content

    return body
