import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta

from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

NULL = -1


@dataclass
class Language:
    days: tuple
    months: tuple


class CallbackFactory:
    def __init__(self, prefix: str, *chunks, sep=" "):
        if not isinstance(prefix, str):
            raise TypeError(
                f"Prefix must be instance of str not {type(prefix).__name__}"
            )
        if not prefix:
            raise ValueError("Prefix must be specified")
        if sep in prefix:
            raise ValueError(f"Separator {sep!r} can't be used in prefix")
        if not chunks:
            raise TypeError("Chunks are not specified")

        self.prefix = prefix
        self.sep = sep
        self._chunks = chunks

    def create(self, *args, **kwargs) -> str:
        """
        Generate callback data
        :param args:
        :param kwargs:
        :return:
        """

        args = list(args)
        data = [self.prefix]

        for chunk in self._chunks:
            value = kwargs.pop(chunk, None)
            if value is None:
                if args:
                    value = args.pop(0)
                else:
                    raise ValueError(f"Value for {chunk} is not specified")

            if value is not None and not isinstance(value, str):
                value = str(value)

            if not value:
                raise ValueError(f"Value for {chunk} must not be empty")

            if self.sep in value:
                raise ValueError(
                    f"Symbol {self.sep} is defined as the separator and can't be used as chunk' values"
                )

            data.append(value)

        if args or kwargs:
            raise TypeError("Too many arguments were passed!")

        callback_data = self.sep.join(data)
        # Reference - https://core.telegram.org/bots/api#inlinekeyboardbutton
        if len(callback_data) > 64:
            raise ValueError("Callback data must within 1-64 bytes")

        return callback_data


class Calendar:
    _language = Language(
        days=("Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"),
        months=(
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
    )

    def create(
        self,
        name: str = "calendar",
        month: int | None = None,
        year: int | None = None,
        delete_upon_completion: bool = True,
    ) -> InlineKeyboardMarkup:
        """
        Creates an inline keyboard with calendar
        :param name: Prefix metadata to be handled with callback queries.
        :param year: Year to use in the calendar if not default.
        :param month: Month to use in the calendar if not default.
        :return: Returns an InlineKeyboardMarkup object with a calendar.
        """
        self._delete_upon_completion = delete_upon_completion
        now = datetime.now()

        if year is None:
            year = now.year
        if month is None:
            month = now.month

        factory = CallbackFactory(name, "action", "day", "month", "year")

        keyboard = InlineKeyboardMarkup(row_width=7)
        self._add_header(keyboard, factory, month, year)
        self._add_days_of_weeks(keyboard, factory)
        self._populate_days_of_month(keyboard, factory, month, year)
        self._add_footer(keyboard, factory, month, year)
        return keyboard

    def _add_header(
        self,
        keyboard: InlineKeyboardMarkup,
        factory: CallbackFactory,
        month: int,
        year: int,
    ) -> None:
        callback_data = factory.create("LIST_MONTHS", NULL, month, year)
        text = f"{self._language.months[month - 1]} {year}"
        keyboard.add(InlineKeyboardButton(text=text, callback_data=callback_data))

    def _add_days_of_weeks(
        self,
        keyboard: InlineKeyboardMarkup,
        factory: CallbackFactory,
    ) -> None:
        callback_data = factory.create("NO-OP", NULL, NULL, NULL)
        buttons = [
            InlineKeyboardButton(text=day, callback_data=callback_data)
            for day in self._language.days
        ]
        keyboard.add(*buttons)

    def _populate_days_of_month(
        self,
        keyboard: InlineKeyboardMarkup,
        factory: CallbackFactory,
        month: int,
        year: int,
    ) -> None:
        no_op = factory.create("NO-OP", NULL, NULL, NULL)

        for week in calendar.monthcalendar(year, month):
            row_buttons = []

            for day in week:
                if day == 0:
                    row_buttons.append(
                        InlineKeyboardButton(text=" ", callback_data=no_op)
                    )
                else:
                    callback_data = factory.create("DAY", day, month, year)
                    row_buttons.append(
                        InlineKeyboardButton(text=day, callback_data=callback_data)
                    )
            keyboard.add(*row_buttons)

    def _add_footer(
        self,
        keyboard: InlineKeyboardMarkup,
        factory: CallbackFactory,
        month: int,
        year: int,
    ) -> None:
        previous = InlineKeyboardButton(
            text="<", callback_data=factory.create("PREVIOUS", NULL, month, year)
        )
        cancel = InlineKeyboardButton(
            text="Cancel", callback_data=factory.create("CANCEL", NULL, month, year)
        )
        next = InlineKeyboardButton(
            text=">", callback_data=factory.create("NEXT", NULL, month, year)
        )
        keyboard.add(previous, cancel, next)

    def _list_months(self, name: str, year: int) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup()
        factory = CallbackFactory(name, "action", "day", "month", "year")

        # Iterates odd and even months
        for i, month in enumerate(
            zip(self._language.months[0::2], self._language.months[1::2])
        ):
            odd = InlineKeyboardButton(
                text=month[0],
                callback_data=factory.create("MONTH", NULL, 2 * i + 1, year),
            )
            even = InlineKeyboardButton(
                text=month[1],
                callback_data=factory.create("MONTH", NULL, 2 * (i + 1), year),
            )
            keyboard.add(odd, even)

        return keyboard

    async def handle_callback(
        self,
        bot: AsyncTeleBot,
        callback: CallbackQuery,
        name: str,
        action: str,
        day: int,
        month: int,
        year: int,
    ) -> None | datetime:
        """
        Updates the calendar text if forward, backward or cancel button is pressed.
        Should be called within a CallbackQueryHandler (i.e. @bot.callback_query_handler(...)).

        :param bot:
        :param call:
        :param day:
        :param month:
        :param year:
        :param action:
        :param name:
        :return:
        """
        if not callback.message.text:
            return

        now = datetime(year, month, 1)

        match action:
            case "IGNORE":
                await bot.answer_callback_query(callback_query_id=callback.id)
            case "PREVIOUS":
                previous = now - timedelta(days=1)
                await bot.edit_message_text(
                    text=callback.message.text,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    reply_markup=self.create(
                        name=name,
                        month=previous.month,
                        year=previous.year,
                        delete_upon_completion=self._delete_upon_completion,
                    ),
                )
            case "NEXT":
                next = now + timedelta(days=31)
                await bot.edit_message_text(
                    text=callback.message.text,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    reply_markup=self.create(
                        name=name,
                        month=next.month,
                        year=next.year,
                        delete_upon_completion=self._delete_upon_completion,
                    ),
                )
            case "LIST_MONTHS":
                await bot.edit_message_text(
                    text=callback.message.text,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    reply_markup=self._list_months(name, year),
                )
            case "DAY":
                if self._delete_upon_completion:
                    await bot.delete_message(
                        chat_id=callback.message.chat.id, message_id=callback.message.id
                    )
                return datetime(year, month, day)
            case "MONTH":
                await bot.edit_message_text(
                    text=callback.message.text,
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    reply_markup=self.create(name, month, year),
                )
            case "CANCEL":
                await bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                )
            case "_":
                await bot.answer_callback_query(
                    callback_query_id=callback.id, text="Something went wrong"
                )
                await bot.delete_message(
                    chat_id=callback.message.chat.id, message_id=callback.message.id
                )
