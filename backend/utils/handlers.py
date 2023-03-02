from typing import Optional, cast

from database import Firestore
from database.models import CustomStates, Responder
from telebot import types
from telebot.async_telebot import AsyncTeleBot

CANCEL_BUTTON = types.InlineKeyboardButton("Cancel", callback_data="cancel")


async def process_welcome_message(
    bot: AsyncTeleBot,
    message: types.Message | int,
    is_edit=False,
    is_delete=False,
    database: Optional[Firestore] = None,
    chat_id: Optional[int] = None,
    responder_id: Optional[int] = None,
) -> None:
    is_onboarded = True
    responder = None
    is_integer = isinstance(message, int)

    try:
        if database:
            responder = await database.get_responder(
                responder_id
                if responder_id is not None
                else cast(types.Message, message).chat.id
            )
    except Exception:
        is_onboarded = False

    # Ignore repeated /start commands
    if is_onboarded and responder is not None and responder.message_id != -1:
        return

    keyboard = types.InlineKeyboardMarkup()
    onboard_button = types.InlineKeyboardButton(
        text="📝 Onboard", callback_data="onboard"
    )
    check_in_button = types.InlineKeyboardButton(
        text="✅ Check-In", callback_data="check_in"
    )
    check_out_button = types.InlineKeyboardButton(
        text="❌ Check-Out", callback_data="check_out"
    )
    profile_button = types.InlineKeyboardButton(
        text="📖 Profile", callback_data="profile"
    )

    # Conditionally render onboard button
    if is_onboarded:
        keyboard.add(profile_button)

        # Dynamically render check-in/out button based on availability
        if responder is not None:
            if responder.is_available:
                keyboard.add(check_out_button)
            else:
                keyboard.add(check_in_button)
        else:
            keyboard.add(check_in_button)
    else:
        keyboard.add(onboard_button)

    if is_edit and not is_delete:
        await bot.edit_message_text(
            chat_id=chat_id if is_integer else message.chat.id,
            message_id=message if is_integer else message.id,
            text="Welcome to ConnectID, below are a list of actions available.",
            reply_markup=keyboard,
        )
        return

    # Special case to handle for location updates, need to delete normal message without inline keyboard
    # else unable to edit the mssage
    if is_delete:
        await bot.delete_message(
            chat_id=cast(int, chat_id) if is_integer else message.chat.id,
            message_id=message if is_integer else message.id,
        )

    message = await bot.send_message(
        chat_id=cast(int, chat_id) if is_integer else message.chat.id,
        text="Welcome to ConnectID, below are a list of actions available.",
        reply_markup=keyboard,
    )

    if database and responder is not None:
        await database.update_latest_bot_message(message.chat.id, message.id)


async def process_profile(
    bot: AsyncTeleBot, database: Firestore, callback: types.CallbackQuery
) -> None:
    responder = await database.get_responder(callback.from_user.id)

    text = "<b>📖  Profile</b>\n\n"
    text += f"<b>Name</b>: <i>{responder.name}</i>\n"
    text += f"<b>Gender</b>: <i>{responder.gender}</i>\n"
    text += f"<b>Date of Birth</b>: <i>{responder.date_of_birth}</i>\n"
    text += f"<b>NRIC</b>: <i>{responder.nric}</i>\n"
    text += f"<b>Phone Number</b>: <i>{responder.phone_number}</i>\n"
    text += f"<b>Address</b>: <i>{responder.address}</i>\n"
    text += f"<b>Medical Knowledge</b>"

    # Handle inexperienced responders
    if len(responder.existing_medical_knowledge) == 0:
        text += ": <i>None</i>"
    else:
        text += "\n"

    for index, medical_knowledge in enumerate(responder.existing_medical_knowledge):
        medical_description = (
            f" - <i>{medical_knowledge.description}</i>"
            if medical_knowledge.description
            else ""
        )
        text += f"{index + 1}. {medical_knowledge.condition}{medical_description}\n"
    text = text.rstrip("\n")
    options = ["➕ Add", "➖ Remove"]
    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(
            option, callback_data=f"option {option.split(' ')[1].lower()}"
        )
        for option in options
    ]
    keyboard.add(*buttons, row_width=2)
    keyboard.add(CANCEL_BUTTON)

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def process_cancel(bot: AsyncTeleBot, callback: types.CallbackQuery) -> None:
    await process_welcome_message(bot=bot, message=callback.message, is_edit=True)
