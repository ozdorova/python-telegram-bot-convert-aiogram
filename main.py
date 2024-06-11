import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.utils import markdown
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import InlineKeyboardBuilder

from packages.config import bot_token
from packages.converter import convert, delete_items_in_folder

dp = Dispatcher()
temp_files = "packages/temp_files/"

supported_extensions = {
    'csv': ['xlsx'],
    'xls': ['csv', 'xlsx'],
    'xlsx': ['csv'],
    'pdf': ['docx'],
    'jpg': ['png'],
    'png': ['jpg'],
    'heic': ['jpg', 'png'],
}


@dp.message(Command("clear", prefix="$"))
async def delete_message(message: types.Message, i: int = 0):
    while True:
        try:
            await message.bot.delete_message(
                message.chat.id,
                message.message_id - i
            )
            i += 1
            continue
        except Exception:
            return


@dp.message(CommandStart())  # /start
async def handle_start(message: types.Message):
    await message.answer(
        text=f"Привет, {markdown.hbold(message.from_user.full_name)}!",
        parse_mode=ParseMode.HTML
    )


def create_buttons(extension):
    try:
        builder = InlineKeyboardBuilder()
        for value in supported_extensions[extension]:
            builder.add(
                types.InlineKeyboardButton(
                    text=value,
                    callback_data=value
                )
            )
        return builder.as_markup()
    except Exception:
        return


@dp.message(F.document)
async def get_document(message: types.Message):
    """
    Принимает входящий файл
    """
    global filename, name, extension, downloadUrl

    fileId = message.document.file_id
    filename = message.document.file_name
    name, extension = filename.split('.')
    file_info = await temp.get_file(file_id=fileId)

    async with ChatActionSender(
        bot=message.bot,
        chat_id=message.chat.id,
        action=ChatAction.TYPING,
    ):
        downloaded_file = await temp.download_file(
            file_info.file_path
        )
        with open(f'{temp_files}{filename}', 'wb') as new_file:
            new_file.write(downloaded_file.getvalue())
    await asyncio.sleep(1)
    try:
        if extension in supported_extensions:
            await message.reply(
                text="Доступные действия:",
                reply_markup=create_buttons(extension.lower())
            )
        else:
            await message.answer(
                text="Данный формат пока не поддерживается 🥲"
            )
    except Exception as e:
        await message.answer(
            text=f"Ошибка 🤯\n{e}"
        )


@dp.callback_query(F.data)
async def callback_message(callback: types.CallbackQuery):
    """
    Отправляет файл по api в convertio,
    затем после получения файла отправляет его ответным сообщением
    """
    # await asyncio.sleep(2)
    await callback.message.bot.delete_message(
        callback.message.chat.id,
        callback.message.message_id - 0
    )
    try:
        async with ChatActionSender(
            bot=callback.message.bot,
            chat_id=callback.message.chat.id,
            action=ChatAction.UPLOAD_DOCUMENT,
        ):
            await asyncio.to_thread(
                convert,
                filename,
                name,
                callback.data
            )
            # TODO: Доработать отправку и получение файла,
            # Обернуть в try except
            while True:
                await asyncio.sleep(4)
                if os.path.isfile(
                    f"{temp_files}{name}.{callback.data}"
                ):
                    break
                else:
                    continue
            await callback.message.bot.send_document(
                chat_id=callback.message.chat.id,
                document=types.FSInputFile(
                    path=f"{temp_files}{name}.{callback.data}"
                ),
                caption="Ваш файл готов! ✅"
            )
    except Exception as err:
        await callback.message.answer(
            f'Возникла ошибка 🤯\n{err}'
        )
        await asyncio.to_thread(delete_items_in_folder)


async def main():
    global temp
    bot = Bot(
        token=bot_token,
        parse_mode=None
    )
    temp = bot
    logging.basicConfig(
        level=logging.INFO,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
