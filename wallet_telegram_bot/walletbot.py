from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

from config import TOKEN

bot = Bot(token=TOKEN) # в отдельном файле config.py нужно вписать токен бота и тут есть применить
dp = Dispatcher(bot)


button_regis = InlineKeyboardButton('Регистрация', callback_data='btn1')
create_regis = InlineKeyboardMarkup().add(button_regis)

# если эта кнопка не нужна, можно убрать эту строку и удалить ".add(button_info)" из 20 строки
button_info = InlineKeyboardButton('Дополнительная информация', callback_data='btn2')

inline_kb_full = InlineKeyboardMarkup(row_width=2).add(button_info)
inline_btn_3 = InlineKeyboardButton('Перевод', callback_data='btn3')
inline_btn_4 = InlineKeyboardButton('Баланс', callback_data='btn4')
inline_kb_full.add(inline_btn_3, inline_btn_4)


# /start
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет!\nНачни пользоваться кошельком, пройдя регистрацию.", reply_markup=create_regis)


# если нажал на кнопку РЕГИСТРАЦИЯ
@dp.callback_query_handler(text='btn1')
async def process_callback_button1(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    await bot.send_message(callback.from_user.id, 'ПРОХОЖДЕНИЕ РЕГИСТРАЦИИ', reply_markup=inline_kb_full)


# если нажал на кнопку ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ (если она не нужна, то эту часть удалить)
@dp.callback_query_handler(text='btn2')
async def process_callback_button2(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    await bot.send_message(callback.from_user.id, 'Дополнительная информация', reply_markup=inline_kb_full)


# если нажал на кнопку ПЕРЕВОД
@dp.callback_query_handler(text='btn3')
async def process_callback_button3(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    await bot.send_message(callback.from_user.id, 'Выполнение перевода', reply_markup=inline_kb_full)


# если нажал на кнопку БАЛАНС
@dp.callback_query_handler(text='btn4')
async def process_callback_button4(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    await bot.send_message(callback.from_user.id, 'Вывод баланса', reply_markup=inline_kb_full)


# /help
@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Я кошелек")


# /nodelist
@dp.message_handler(commands=['nodelist'])
async def process_help_command(message: types.Message):
    await message.reply("СПИСОК НОД:")


# введено ЛЮБОЕ ДРУГОЕ СООБЩЕНИЕ КРОМЕ ЗАПРОГРАММИРОВАННЫХ
@dp.message_handler()
async def process_help_command(message: types.Message):
    await message.reply("Я тебя не понимаю. Для работы с кошельком воспользуйся кнопками.")


if __name__ == '__main__':
    executor.start_polling(dp)
