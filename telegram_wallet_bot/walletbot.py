import logging
from asyncio import sleep
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage


from config import TOKEN, BYTES
import hashlib
import requests
import sqlite3
import rsa


logging.basicConfig(level=logging.INFO) # логгирование для удобства

bot = Bot(token=TOKEN)  # в отдельном файле config.py нужно вписать токен бота и тут есть применить

storage = MemoryStorage()  # установка хранилища данных для функции перевода
dp = Dispatcher(bot, storage=storage)

database = sqlite3.connect('users.db')  # подключаем БД. Если БД с таким названием нет, должна создаться сама
cur = database.cursor()

try:
    cur.execute("CREATE TABLE users ("          # Создаем БД
                    "id_telegram INT PRIMARY KEY,"
                    "balance FLOAT,"
                    "public_key VARCHAR(255),"
                    "private_key VARCHAR(255),"
                    "reputation INT,"
                    "wallet_address VARCHAR(255));")

except sqlite3.OperationalError:  # Если такая БД уже есть, просто идем дальше
    pass

button_regis = InlineKeyboardButton('Регистрация', callback_data='btn1')
create_regis = InlineKeyboardMarkup().add(button_regis)

# если эта кнопка не нужна, можно убрать эту строку и удалить ".add(button_info)" из 20 строки
button_info = InlineKeyboardButton('FAQ', callback_data='btn2')

inline_kb_full = InlineKeyboardMarkup(row_width=2).add(button_info)
inline_btn_3 = InlineKeyboardButton('Перевод', callback_data='btn3')
inline_btn_4 = InlineKeyboardButton('Баланс', callback_data='btn4')
inline_kb_full.add(inline_btn_3, inline_btn_4)


# /start
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    global user_id
    user_id = message.chat.id  # Определяем ID telegram-аккаунта юзера, чтобы узнать есть ли он у нас в БД

    cur.execute("SELECT * FROM users WHERE id_telegram = '" + str(user_id) + "';")  # Ищем его в БД

    if len(cur.fetchall()) == 0:  # Грубо говоря, если юзера в БД нет - выводим ему сообщение с приглашением на регистрацию и соответствующий набор кнопок
        await message.reply("Привет!\nНачни пользоваться кошельком, пройдя регистрацию.", reply_markup=create_regis)
    else:  # В ином случае - сразу приглашаем к взаимодействию с ботом
        await message.reply("Пользователь опознан", reply_markup=inline_kb_full)


# если нажал на кнопку РЕГИСТРАЦИЯ
@dp.callback_query_handler(text='btn1')
async def process_callback_button1(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)

    (PUBLIC_KEY, PRIVATE_KEY) = rsa.newkeys(BYTES)  # Генерируем пару ключей (регистрируем пользователя)
    user_id = callback.message.chat.id  # Получаем ID пользователя (ID чата и ID пользователя совпадаюат)
    wallet_address = hashlib.md5(str(user_id).encode())  # Генерируем кошелек для пользователя (кошелек = хешированный с помощью SHA256 ID telegram-аккаунта пользователя)

    data_tuple = (user_id, 0,
                  str(PUBLIC_KEY),
                  str(PRIVATE_KEY), 0,
                  str(wallet_address.hexdigest()))  # формируем кортеж из данных которые необходимо занести в таблицу

    cur.execute("INSERT INTO users (id_telegram, balance, public_key, private_key, reputation, wallet_address) VALUES "
                "(?, ?, ?, ?, ?, ?);", data_tuple)  # заносим данные след.образом. Данный метод предотвращает возможность SQL-инъекции
    database.commit()

    await bot.send_message(callback.from_user.id, f"Регистрация завершена, ваш ID : {user_id}, "
                                                  f"ваш пуб.ключ: {PUBLIC_KEY}, "
                                                  f"ваш прив.ключ: {PRIVATE_KEY}, "
                                                  f"ваш адрес кошелька: ' {wallet_address}",
                           reply_markup=inline_kb_full) # Информацию о ключах, ID и проч. выводил для дебаггинга.

    '''Адрес кошелька пользователя - хеш (SHA256) от его telegram ID (выглядеть в таблице должно след.образом: 
    abe29babbdf5c71122ee439379f6fa808de71f2f5d2a23aaf11db65ac). На данный момент это дело выглядит так:  
    sha256 _hashlib.HASH object @ 0x0000019C7438FF50 (возможно дело в каком-то форматировании. Нужно пофиксить'''


# если нажал на кнопку ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ (если она не нужна, то эту часть удалить)
@dp.callback_query_handler(text='btn2')
async def process_callback_button2(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    await bot.send_message(callback.from_user.id, 'Дополнительная информация', reply_markup=inline_kb_full)


# если нажал на кнопку ПЕРЕВОД
# первым делом объявляется класс для хранения данных о переводе: адрес кошелька и сумма перевода
class TransferStates(StatesGroup):
    receiver = State()
    value = State()


@dp.callback_query_handler(text='btn3')
async def process_callback_button3(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    await bot.send_message(callback.from_user.id, 'Для выполнения перевода, *укажите адрес кошелька получателя.*', parse_mode="Markdown")
    # переводим бота в состояние ожидания ввода адреса
    await TransferStates.receiver.set()


# обработчик введенного адреса
"""
    Принимает от пользователя сообщение с адресом, проверяет его, запоминает и переводится в состояние TransferStates.value,
    где будет ждать ввода суммы перевода.
"""
@dp.message_handler(state=TransferStates.receiver)
async def process_wallet_receiver(message: types.Message, state: FSMContext):
    if len(message.text) != 32:
        # предварительная проверка на верную длину адреса
        # если он меньше 32 символов - вышвыриваем пользователя обратно в меню
        await message.reply("❗* Адрес получателя указан неверно.*", parse_mode="Markdown", reply_markup=inline_kb_full)
        await state.finish()
    elif len(message.text) == 32:
        # если длина верная, ищем его в БД
        cur.execute("SELECT * FROM users WHERE wallet_address = '" + str(message.text) + "';")  # Ищем его в БД

        if len(cur.fetchall()) == 0:
            # адрес не найден - пользователь выкидывается в меню
            await message.reply("❗* Адрес получателя не найден. Пожалуйста, проверьте корректность введенных данных.*",
                                parse_mode="Markdown", reply_markup=inline_kb_full)
            await state.finish()
        else:
            # адрес найден - выводится запрос на ввод суммы перевода и бот переводится в режим ожидания ввода
            await state.update_data(receiver=message.text)
            await message.reply(f"Адрес получателя _{message.text}._", parse_mode="Markdown")
            await message.answer(f"*Укажите сумму перевода.*", parse_mode="Markdown")
            await TransferStates.value.set()


# обработчик введенной суммы
"""
    Принимает от пользователя сообщение с суммой и тоже сохраняет ее в хранилище состояний,
    а затем переводится в состояние обработки запроса на перевод.
"""
@dp.message_handler(state=TransferStates.value)
async def process_value(message: types.Message,  state: FSMContext):
    if message.text.isdigit(): # если введенная сумма состоит из цифр, запрос проходит успешно
        await state.update_data(value=message.text)

        # вывод сохраненных переменных с данными из хранилища состояний
        data = await state.get_data()
        receiver = data.get("receiver")
        value = data.get("value")

        print(receiver, value) # просто так

        # отправляем пользователю сообщения
        await message.reply(f"*Запрошен перевод на адрес* _{receiver}_ *суммой* _{value}_.", parse_mode="Markdown")

        msg = await bot.send_message(message.from_user.id, "*Проверка наличия средств на счете 🕛...*", parse_mode="Markdown")
        msg1 = await msg.edit_text("*Проверка наличия средств на счете 🕐...*", parse_mode="Markdown")
        await sleep(1)
        msg2 = await msg1.edit_text("*Проверка наличия средств на счете 🕑...*", parse_mode="Markdown")
        await sleep(1)
        msg3 = await msg2.edit_text("*Проверка наличия средств на счете 🕒...*", parse_mode="Markdown")
        await sleep(1)
        msg4 = await msg3.edit_text("*Проверка наличия средств на счете 🕓...*", parse_mode="Markdown")
        await sleep(1)
        msg5 = await msg4.edit_text("*Проверка наличия средств на счете 🕔...*", parse_mode="Markdown")
        await sleep(1)
        msg6 = await msg5.edit_text("*Проверка наличия средств на счете 🕕...*", parse_mode="Markdown")

        # запрос на вывод баланса пользователя
        user = cur.execute(f'SELECT * FROM users WHERE id_telegram ={user_id}').fetchone()
        print(user[1]) # просто так
        await message.answer(f"*Средств на счете:* _{user[1]}_.", parse_mode="Markdown")

        if user[1] < float(value): # если баланс меньше переводимой суммы - отсылаем в меню
            await message.answer("*❗ Недостаточно средств на счете.\nПополните его и вернитесь позже.*",
                                 parse_mode="Markdown", reply_markup=inline_kb_full)
            await state.finish()
        if user[1] >= float(value): # если все ОК, оповещаем пользователя и обновляем значение его баланса в БД
            await bot.send_message(message.from_user.id, f'✅Перевод выполнен успешно.\nТекущий баланс: '
                                                         f'_{user[1] - float(value)}_', parse_mode="Markdown",
                                                         reply_markup=inline_kb_full)
            update_balance = cur.execute(f'UPDATE users SET balance = {user[1] - float(value)} '
                                         f'WHERE id_telegram ={user_id}').fetchone()
        await state.finish()

    if not message.text.isdigit(): # если в указанной сумме есть что-то кроме цифр - отсылка в меню
        await message.reply("❗*Сумма перевода указана неверно.*", parse_mode="Markdown",
                            reply_markup=inline_kb_full)
        await state.finish()


        # requests.post('http://127.0.0.1:5000/transactions/new', json = {"privkey": "PrivateKey(22007182649237165642039897168970460211417563048076076057230300742488044918525379770177118397160839085570764232781348589172871368559518315381715717913628226700482497434709928601002387888895465078083009506011166982716498575163002231043515345202143560364953071616933419478345658375240770902514502944866420238056517112082758891921677969504569769108559812844698270601108511582498253228371031456043689461760887236718395544915148541024883395814430748543137760737450813473339219902728827092484701284544493764769140866335511781526459449788784795552683725790971800480660034754332836115007003064144357286491068461245812519385149, 65537, 16859401853460646282098617836680041744886729449849024987493503049851187439528872882818599926244018614969427343870686308750817901357519203814178266464585385018403722305025884390047254050960138779243994358428104135087770937992414254756881989358133905049715410633251082468671139509677180595730990886433027922614805289105203967394287139507050461942568180875986776272959163218629035024230374393456012908448192282008810340910747501815150175070885099629678498817644355430864818562976742186130836609263445033379775127891805398503347877949436010564233762918608242040709138742776239963953618158971063788089134658049922294108193, 2463792474097435172327771311795631597025137772235523676240704082816072600457422999848960426957849496520179719491529171052658969310868289828320667625476951744995378649054863014052253190564032070988517275207629182518067945068851721196706034652569850262602772402553677437226933148406909860777139596713051545174117639004915052426041, 8932238766294263555970751852812524503844575652438410930061147207961751332453299676703107915160028389792815156496235612844718873864946378728725547350989124859128641334426731899322715983626809952038955455847908336106644618787825303636761936451023580944698584357499151000906882459238387767589)",
   #                                                                 "pubkey": "PublicKey(22007182649237165642039897168970460211417563048076076057230300742488044918525379770177118397160839085570764232781348589172871368559518315381715717913628226700482497434709928601002387888895465078083009506011166982716498575163002231043515345202143560364953071616933419478345658375240770902514502944866420238056517112082758891921677969504569769108559812844698270601108511582498253228371031456043689461760887236718395544915148541024883395814430748543137760737450813473339219902728827092484701284544493764769140866335511781526459449788784795552683725790971800480660034754332836115007003064144357286491068461245812519385149, 65537)",
   #                                                                 "sender": "30d5eacf341bcb4f1c7bf26223736539",
   #                                                                 "receiver": "he",
   #                                                                 "value": 100})

   # await bot.send_message(callback.from_user.id, 'Перевод выполнен', reply_markup=inline_kb_full)
    '''Адаптировал блокчейн под взаимодействие с данным методом. Запрос выше - тестовый. У пользователя должны
    запрашиваться кошелек куда мы совершаем перевод (получатель), кол-во переводимой криптовалюты. Данные значения
    должны сохраняться в некоторые переменные, после чего проверяется есть ли на балансе пользователя достаточное
    кол-во криптовалюты для перевода и есть ли в БД адрес кошелька на который мы собираемся оформить перевод. 
    Если все есть - генерируем запрос с помощью requests.post и всеми ранее запрошенными данными, иначе - выводим сообщение об ошибке
    '''


# если нажал на кнопку БАЛАНС
@dp.callback_query_handler(text='btn4')
async def process_callback_button4(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    user = cur.execute(f'SELECT * FROM users WHERE id_telegram ={user_id}').fetchone()  # запрос на вывод
    print(user[1])
    await bot.send_message(callback.from_user.id, f"*✅Средств на счете:* _{user[1]}_.", parse_mode="Markdown",
                           reply_markup=inline_kb_full)


    # requests.post('http://127.0.0.1:5000/users/get_balance', json = {'address': 'none'})
    # await bot.send_message(callback.from_user.id, 'Вывод баланса', reply_markup=inline_kb_full)

    '''Аналогично предыдущему методу. Параметр address в JSON должен находиться автоматически в БД,
    на основе ID пользователя'''


# /help
@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Я кошелек")


# /nodelist
@dp.message_handler(commands=['nodelist'])
async def process_help_command(message: types.Message):
    res = requests.get('http://127.0.0.1:5000/nodes/total_nodes')
    data = res.json()
    nodes = []
    for i in data['total_nodes']:
        nodes.append(i)

    print(nodes)

    await message.reply("СПИСОК НОД: " + str(nodes))

    ''' Данный метод не должен быть доступен пользователю. Он должен выполняться автоматически и автоматически
    определять наиболее подходящую ноду (на основе пинга). С самой близкой нодой бот и должен взаимодействовать
    '''


# введено ЛЮБОЕ ДРУГОЕ СООБЩЕНИЕ КРОМЕ ЗАПРОГРАММИРОВАННЫХ
@dp.message_handler()
async def process_help_command(message: types.Message):
    await message.reply("Я тебя не понимаю. Для работы с кошельком воспользуйся кнопками.")


if __name__ == '__main__':
    executor.start_polling(dp)
