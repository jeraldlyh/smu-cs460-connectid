import asyncio
from typing import cast

from database import Firestore
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from utils.handlers import process_welcome_message


def _get_check_in_out_message(check_in=True):
    return f"You have successfully checked {'in' if check_in else 'out'}. You'll{'' if check_in else ' not'} receive any notifications if a distress signal is issued in the vicinity."


async def process_check_in(
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    button = types.KeyboardButton(text="Send location", request_location=True)
    markup.add(button)
    await bot.delete_message(
        chat_id=callback.message.chat.id, message_id=callback.message.id
    )
    message = await bot.send_message(
        chat_id=callback.message.chat.id,
        text="❗ Click on the button below to send your location",
        reply_markup=markup,
    )

    responder = await database.get_responder(callback.message.chat.id)
    responder.message_id = message.id
    await database.update_responder(responder)


async def process_check_out(
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    responder = await database.get_responder(callback.message.chat.id)

    responder.is_available = False
    await database.update_responder(responder)

    notification = await bot.send_message(
        chat_id=callback.message.chat.id,
        text=_get_check_in_out_message(False),
    )
    await asyncio.sleep(3)
    await bot.delete_message(
        chat_id=callback.message.chat.id, message_id=notification.id
    )
    await process_welcome_message(
        bot=bot, message=callback.message, is_edit=True, database=database
    )


async def process_location(
    bot: AsyncTeleBot, database: Firestore, message: types.Message
) -> None:
    responder = await database.get_responder(message.chat.id)

    responder.is_available = True
    responder.location = {
        "longitude": cast(types.Location, message.location).longitude,
        "latitude": cast(types.Location, message.location).latitude,
    }
    await database.update_responder(responder)

    notification = await bot.send_message(
        chat_id=message.chat.id,
        text=_get_check_in_out_message(),
    )
    await asyncio.sleep(3)
    await bot.delete_message(chat_id=message.chat.id, message_id=notification.id)
    await process_welcome_message(
        bot=bot,
        message=responder.message_id,
        database=database,
        chat_id=message.chat.id,
        is_edit=True,
        is_delete=True,
        responder_id=responder.telegram_id,
    )
