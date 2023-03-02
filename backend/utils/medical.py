import asyncio
from datetime import datetime
from typing import List

from database import Firestore
from database.models import CustomStates, ExistingMedicalKnowledge, Responder
from telebot import types
from telebot.async_telebot import AsyncTeleBot

from utils.handlers import CANCEL_BUTTON, process_welcome_message

MEDICAL_CONDITIONS = [
    "Fragile X syndrome",
    "Down syndrome",
    "Developmental delay",
    "Prader-Willi Syndrome (PWS)",
    "Fetal alcohol spectrum disorder (FASD)",
]


def _get_list_of_existing_experience(responder: Responder) -> List[str]:
    return (
        [experience.condition for experience in responder.existing_medical_knowledge]
        if len(responder.existing_medical_knowledge) != 0
        else []
    )


async def process_list_medical_conditions(
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    responder = await database.get_responder(callback.from_user.id)
    existing_experience = _get_list_of_existing_experience(responder)

    keyboard = types.InlineKeyboardMarkup()
    options = list(
        filter(
            lambda x: x not in existing_experience,
            MEDICAL_CONDITIONS,
        )
    )

    if len(options) == 0:
        message = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=(
                "You already possess all the medical conditions available in the system. Do contact our staffs at +65 9812 3456 if you deem that this condition is necessary."
            ),
        )
        await asyncio.sleep(3)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.id)
        return

    buttons = [
        types.InlineKeyboardButton(option, callback_data=f"option add {option}")
        for option in options
    ]
    keyboard.add(*buttons, row_width=2)
    keyboard.add(CANCEL_BUTTON)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=("Kindly choose one of the options below."),
        reply_markup=keyboard,
    )


async def process_add_medical_condition(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    condition: str,
) -> None:
    # Add a new condition
    responder = await database.get_responder(callback.from_user.id)
    responder.existing_medical_knowledge.append(
        ExistingMedicalKnowledge(condition=condition, created_at=str(datetime.now()))
    )
    responder.state = CustomStates.EXISTING_MEDICAL_KNOWLEDGE
    await database.update_responder(responder)

    # Proceeds to next step of adding condition description
    keyboard = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("Skip", callback_data="option skip")
    keyboard.add(cancel_button)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=(
            f"Kindly provide a short description with <b>{condition}</b> in less than 30 words. If you do not have any description, do proceed to press skip."
        ),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def process_skip_description(
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    responder = await database.get_responder(callback.from_user.id)
    responder.state = CustomStates.NOOP
    await database.update_responder(responder)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=(f"You have successfully updated your profile."),
    )

    await asyncio.sleep(3)
    await process_welcome_message(bot=bot, message=callback.message, is_edit=True)


async def process_add_medical_condition_description(
    bot: AsyncTeleBot, responder: Responder, message: types.Message
) -> bool:
    sorted_medical_conditions = sorted(
        responder.existing_medical_knowledge,
        key=lambda x: x.created_at,
        reverse=True,
    )

    sorted_medical_conditions[0].description = message.text
    responder.existing_medical_knowledge = sorted_medical_conditions
    responder.state = CustomStates.NOOP

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=responder.message_id,
        text=(
            f"You have successfully added a description to {sorted_medical_conditions[0].condition}."
        ),
    )
    await asyncio.sleep(3)
    await process_welcome_message(
        bot=bot, message=responder.message_id, chat_id=message.chat.id, is_edit=True
    )
    return True


async def process_list_existing_medical_condition(
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    responder = await database.get_responder(callback.from_user.id)
    existing_experience = _get_list_of_existing_experience(responder)

    if len(existing_experience) == 0:
        notification = await bot.send_message(
            chat_id=callback.message.chat.id, text="You do not any medical experiences."
        )
        await asyncio.sleep(3)
        await bot.delete_message(
            chat_id=callback.message.chat.id, message_id=notification.id
        )
        return

    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(option, callback_data=f"option remove {option}")
        for option in existing_experience
    ]
    keyboard.add(*buttons, row_width=2)
    keyboard.add(CANCEL_BUTTON)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=(f"Kindly choose the medical condition that you wish to remove."),
        reply_markup=keyboard,
    )


async def process_remove_medical_condition(
    bot: AsyncTeleBot,
    database: Firestore,
    callback: types.CallbackQuery,
    condition: str,
) -> None:
    responder = await database.get_responder(callback.from_user.id)
    responder.existing_medical_knowledge = list(
        filter(
            lambda x: x.condition != condition,
            responder.existing_medical_knowledge,
        )
    )

    await database.update_responder(responder)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=(
            f"You have successfully removed <b>{condition}</b> from your experiences."
        ),
        parse_mode="HTML",
    )
    await asyncio.sleep(3)
    await process_welcome_message(
        bot=bot,
        message=callback.message.id,
        chat_id=callback.message.chat.id,
        is_edit=True,
    )
