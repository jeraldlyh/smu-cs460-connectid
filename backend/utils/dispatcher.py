import asyncio
from datetime import datetime

from database import Firestore
from database.models import Distress, Responder
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from utils import get_group_chat_id
from utils.url import _get_google_maps_link


def _get_anchor_tag(distress: Distress) -> str:
    return f"<a href='{_get_google_maps_link(distress.location.address)}'>{(distress.location.address)}</a>"


async def process_manual_acknowledge_distress(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    group_chat_message_id: int,
) -> None:
    distress = await database.get_distress(group_chat_message_id)
    distress.is_acknowledged = True
    distress.acknowledged_at = str(datetime.now())
    distress.is_completed = True

    await database.update_distress(distress)

    # Responder message
    if distress.responder is not None:
        await bot.edit_message_text(
            chat_id=distress.responder.telegram_id,
            message_id=distress.message_id,
            text=f"This distress signal has been taken over by the dispatchers.",
        )
        await asyncio.sleep(3)
        await bot.delete_message(
            chat_id=distress.responder.telegram_id, message_id=distress.message_id
        )

    # Dispatcher group chat message
    text = "<b>❗ Distress Signal ❗</b>\n\n"
    text += "<b>Status: </b> 🟢 Completed\n\n"
    text += f"@{callback.from_user.username} has taken over this signal to assist <b>{distress.pwid.name}</b> at {_get_anchor_tag(distress)}\n\n"

    await bot.edit_message_text(
        chat_id=get_group_chat_id(),
        message_id=distress.group_chat_message_id,
        text=text,
        parse_mode="HTML",
    )


async def process_false_distress(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    group_chat_message_id: int,
) -> None:
    print("here")
    distress = await database.get_distress(group_chat_message_id)
    print("her2")
    distress.is_acknowledged = True
    distress.acknowledged_at = str(datetime.now())
    distress.is_completed = True

    await database.update_distress(distress)

    # Responder message
    if distress.responder is not None:
        await bot.edit_message_text(
            chat_id=distress.responder.telegram_id,
            message_id=distress.message_id,
            text=f"This distress signal is deemed to be a false signal by the dispatchers. Apologies for any inconvenience caused.",
        )
        await asyncio.sleep(3)
        await bot.delete_message(
            chat_id=distress.responder.telegram_id, message_id=distress.message_id
        )

    # Dispatcher group chat message
    text = "<b>❗ Distress Signal ❗</b>\n\n"
    text += "<b>Status: </b> ⚫ Cancelled\n\n"
    text += f"This signal to assist <b>{distress.pwid.name}</b> at {_get_anchor_tag(distress)} has been cancelled by @{callback.from_user.username}\n\n"

    await bot.edit_message_text(
        chat_id=get_group_chat_id(),
        message_id=group_chat_message_id,
        text=text,
        parse_mode="HTML",
    )
