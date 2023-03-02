import asyncio
from datetime import datetime

from database import Firestore
from database.models import (
    Acknowledgement,
    CustomStates,
    ExistingMedicalKnowledge,
    Responder,
)
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from utils.url import _get_google_maps_link


async def process_acknowledge_distress(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    distress_id: str,
) -> None:
    distress = await database.get_distress(distress_id)
    distress.is_acknowledged = True
    distress.acknowledged_at = str(datetime.now())

    await database.update_distress(distress)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=f"You have acknowledged this distress signal. Kindly head over to <a href='{_get_google_maps_link(distress.location)}'>{(distress.location)}</a>",
        parse_mode="HTML",
    )

    responder = await database.get_responder(callback.message.chat.id)
    responder.distress_signals.append(
        Acknowledgement(name=distress.pwid.name, location=distress.location)
    )
    await database.update_responder(responder)

    await asyncio.sleep(10)
    await bot.delete_message(
        chat_id=callback.message.chat.id, message_id=callback.message.id
    )
