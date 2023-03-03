import asyncio
from datetime import datetime
from typing import cast

from database import Firestore
from database.models import Distress, Responder
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from utils import get_group_chat_id
from utils.url import _get_google_maps_link


def _get_anchor_tag(distress: Distress) -> str:
    return f"<a href='{_get_google_maps_link(distress.location.address)}'>{(distress.location.address)}</a>"


async def process_acknowledge_distress(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    group_chat_message_id: int,
) -> None:
    distress = await database.get_distress(group_chat_message_id)
    distress.is_acknowledged = True
    distress.acknowledged_at = str(datetime.now())

    await database.update_distress(distress)

    anchor_tag = _get_anchor_tag(distress)

    # Responder message
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=f"You have acknowledged this distress signal. Kindly head over to {anchor_tag}",
        parse_mode="HTML",
    )

    # Dispatcher group chat message
    keyboard = types.InlineKeyboardMarkup()
    decline = types.InlineKeyboardButton(
        text="❌ Cancel",
        callback_data=f"dispatcher cancel {distress.group_chat_message_id}",
    )
    keyboard.add(decline)
    text = "<b>❗ Distress Signal ❗</b>\n\n"
    text += "<b>Status: </b> 🟠 Acknowledged\n\n"
    text += f"<b>{cast(Responder, distress.responder).name}</b> is on the way to assist {distress.pwid.name} at {anchor_tag}\n\n"
    text += "<i>If you think that this is a false signal, please proceed to cancel this signal.</i>"

    await bot.edit_message_text(
        chat_id=get_group_chat_id(),
        message_id=distress.group_chat_message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def process_reject_distress(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    group_chat_message_id: int,
) -> None:
    distress = await database.get_distress(group_chat_message_id)
    distress.message_id = -1
    await database.update_distress(distress)
    # TODO: add to cron job

    # Responder message
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=f"You have rejected this distress signal. Do kindly check out of the system if you are unavailable.",
        parse_mode="HTML",
    )

    # Dispatcher group chat message
    keyboard = types.InlineKeyboardMarkup()
    accept = types.InlineKeyboardButton(
        text="✅ Accept",
        callback_data=f"dispatcher accept {distress.group_chat_message_id}",
    )
    decline = types.InlineKeyboardButton(
        text="❌ Cancel",
        callback_data=f"dispatcher decline {distress.group_chat_message_id}",
    )
    keyboard.add(accept, decline, row_width=2)

    text = "<b>❗ Distress Signal ❗</b>\n\n"
    text += "<b>Status: </b> 🔴 Not Acknowledged\n\n"
    text += f"<b>{cast(Responder, distress.responder).name}</b> is unavailable at the moment to assist <b>{distress.pwid.name}</b> at {_get_anchor_tag(distress)}. The system will proceed to look for another responder. If you think this distress signal is urgent, kindly manage it manually.\n\n"
    text += "<i>If you think that this is a false signal, please proceed to cancel this signal.</i>"

    await bot.edit_message_text(
        chat_id=get_group_chat_id(),
        message_id=distress.group_chat_message_id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    # Clean up message in responder chat
    await asyncio.sleep(3)
    await bot.delete_message(
        chat_id=callback.message.chat.id, message_id=callback.message.id
    )
