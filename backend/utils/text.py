from database.models import PWID, Distress, Responder
from telebot.formatting import hbold, hitalic

from utils.url import _get_google_maps_link


def format_form_text(responder: Responder, content: str) -> str:
    body = f"<b>Onboarding Form | Step {responder.state.value}</b>"
    body += "\n\n"
    body += content

    return body


# def format_distress_signal_message(
#     pwid: PWID,
#     responder: Responder | None = None,
#     distress: Distress | None = None,
#     is_dispatcher: bool = False,
#     address: str = "",
# ) -> str:
#     pwid_location = address if address else cast(Distress, distress).location.address
#     text = "<b>❗ Distress Signal ❗</b>\n\n"

#     if is_dispatcher:
#         text += f"<b>Status: </b> {_get_status(distress)}\n\n"

#         if responder is None:
#             text += "There's no responders available at this moment. Kindly handle this signal manually or wait for the system to look for a responder."
#         else:
#             text += f"A message has been sent out to <b>{responder.name}</b> to request for assistance."
#         text += "\n\n<i>If you think that this is a false signal, please proceed to cancel this signal.</i>"
#     else:
#         text += f"<b>{pwid.name}</b> is in need of help now. He's currently located at <a href='{_get_google_maps_link(pwid_location)}'>{pwid_location}</a>.\n\n"
#         text += "Kindly acknowledge this message within 30 seconds."

#     return text


def _get_status(distress: Distress | None) -> str:
    if distress is None:
        return "🔴 Not Acknowledged"
    if distress.is_acknowledged:
        return "🟠 Acknowledged"
    elif distress.is_completed:
        return "🟢 Completed"
    return "🔴 Not Acknowledged"


def _get_pwid_contacts(pwid: PWID) -> str:
    text = f"<b>Emergency Contacts:</b> "

    if len(pwid.emergency_contacts) > 0:
        for contact in pwid.emergency_contacts:
            text += f"{contact.name} ({contact.relationship})- {contact.phone_number}, "
    else:
        text += "None"
    text = text.rstrip(", ")
    text += "\n\n"
    return text
