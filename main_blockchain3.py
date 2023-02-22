'''
Общее положение на 22.02.2023

Практически завершен PoI, сформированы полные структуры транзакций и блоков.
Добавлены критерии проверки на валидность для блоков.

Осталось по большей части разобраться с цифровыми подписями, т.к. транзакции
должен подписывать цифровой подписью тот, кто ее формирует. Блоки должны
подписывать валидаторы. Пока не додумался и не раскурил, как лучше эти самые подписи генерировать,
ведь еще необходимо иметь способ проверить их валидность и при этом не допустить
дикой уязвимости.

Из иных вещей, которые еще нужно будет реализовать:
1.Хранилище (как говорил, нужно вести учёт, сколько крипты сейчас вертится в сети). Из
хранилища будут выделяться первые монеты майнерам, за счет него и будем вести учет
2.API. Нужно взаимодействовать с блокчейном посредством HTTP-запросов, сделаем это как и
говорили - через Flask. Прикрутим, когда основной код будет завершен
3.CLI-приложение для клиента. Тестовое клиентское приложение для терминала, чтобы потестить
основные аспекты работы
4.Приложение-нода. Отдельная часть, чем-то схожая с клиентским приложением, но для майнеров

'''

from hashlib import sha256
# from time import time
# import json
from datetime import datetime
import threading, sqlite3
from queue import Queue, Empty
from random import choice, random, getrandbits

try:                                                              #БД с валдиторами (нужно будет заменить хотя-бы на MySQL, т.к. Sqlite3 работает только локально)
    print('Connection to validators database...')
    validators_database = sqlite3.connect('validators.db', timeout=30)
    cursor = validators_database.cursor()
    print("Validators database's connected")
except:
    print('Validators database connection is failed')

class ODS_blockchain():
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.My_Lock = threading.Lock()
        self.temp_blocks = []
        self.candidate_blocks = Queue()
        self.validators = {}

        self.genesis_block = {
            "index": 0,
            'previous_hash': 'None',
            'timestamp': str(datetime.now()),
            'transactions': self.current_transactions,
            'validator': 'None',
            'validator_signature': 'None',

        }
        self.genesis_block['current_hash'] = self.calc_hash(self.genesis_block)
        print(self.genesis_block)
        self.chain.append(self.genesis_block)

        #thread_canditate = threading.Thread(target=self.candidate, args=(self.candidate_blocks,), daemon=True)
        #thread_pick = threading.Thread(target=self.proof_of_importance(), daemon=True)

        #thread_canditate.start()
        #thread_pick.start()

    def new_block(self, address, validator_signature, previous_hash=None):                #Процедура генерации блока
        """
            :param oldblock:
            :param address:
            :param validator_reputation:
            :param previous_hash:
            :return:
            """

        block = {
            'index': len(self.chain) + 1,                   #Убрал 'oldblock', т.к. возникла проблема для создания блока после выбора валидатора (нечего передавать
            'previous_hash': self.hash(self.chain[-1]),     #в качестве аргумента для oldblock)
            'timestamp': str(datetime.now()),
            'transactions': self.current_transactions,
            'validator': address,
            'validator_signature': validator_signature,
        }

        self.current_transactions = []

        block['current_hash'] = self.calc_hash(block)
        return block

    def is_block_valid(self, block, chain):         #Внес изменения из-за удаления 'oldblock'. Добавил проверку по временному штампу и цифровой подписи валидатора
        """
        :param block:
        :param oldblock:
        :return:
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            if block['previous_hash'] != self.hash(last_block):
                return False

            if block['timestamp'] == self.last_block.timestamp:
                return False

            if block['validator_signature'] == self.last_block.validator_signature: #Не корректная проверка. Должна проверяться цифровая подпись валидатора
                return False                                                        #на валидность. Нужно исправить

        last_block = block
        current_index += 1

        return True

    def is_transaction_valid(self):
        '''
        Нужно реализовать проверку транзакций на:
        1)'random_bytes' отличаются друг от друга в каждой транзакции
        2)'sender_signature' - цифровая подпись транзакции ДЕЙСТВИТЕЛЬНА
        '''
        pass

    def new_transactions(self, sender, recipient, amount, sender_signature, oldblock): # Процедура генерации транзакции для блока
        random_bytes =  random.getrandbits(128)

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'random_bytes': random_bytes,                                           #Рандомные байты - своеобразный "идентификатор" транзакции. Уменьшает шанс
            'previous_hash': self.hash(self.chain[-1]),                             #возможности создания дубликата этой транзакции
            'current_hash': self.calc_hash(sender, recipient, amount, random_bytes, self.hash(self.chain[-1])),
            'sender_signature': sender_signature,
        })

        return self.last_block['index'] + 1

    def proof_of_importance(self):
        cursor.execute("""SELECT * FROM validators WHERE reputation = (SELECT max(reputation) from validators)""") #Из БД вытаскиваем адреса валидаторов с наибольшей репутацией
        results = cursor.fetchall()

        '''
        За основу взял твой алгоритм, но переделал под работу с БД. 
        Нужно, чтобы:
        1)Из БД извлекались адреса которым присвоена наибольшая репутация (структура БД ниже)
        2)Если таких несколько - закидываем в lottery_pool и случайно определяем победителя.
        Случайно выбранный победитель создает блок
        3)Если наибольшая репутация только у одного - создаем блок 
        
        Обрати внимание, валидаторы должны подписывать блок своей цифровой подписью (которую еще нужно сгнерерировать 
        и создать способ проверить ее на валидность). Их цифровая подпись передается вторым аргументом в методе new_block
        '''
        if len(results) > 1:
            lottery_pool = []
            for user_address in results:
                lottery_pool.append(user_address)

            lottery_winner = choice(lottery_pool)
            print('Lottery winner is ' + lottery_winner)
            #block = ODS_blockchain.new_block(results, )

        else:
            pass
            #block = ODS_blockchain.new_block(results, )

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def calc_hash(block):
        record = "".join([
            str(block["index"]),
            str(block['previous_hash']),
            block['timestamp'],
            str(block['transactions']),
            str(block["validator"]),
            str(block['validator_signature']),
        ])

        return sha256(record.encode()).hexdigest()


if __name__ == '__main__':
    ODS_blockchain()

'''
CREATE TABLE validators (
user_address TEXT NOT NULL, 
reputation INTEGER NOT NULL,

PRIMARY KEY(user_address)
);

INSERT INTO validators (user_address, reputation) VALUES ('38a88erj3483j4834834', 30);      - тестовое значение 
INSERT INTO validators (user_address, reputation) VALUES ('fdf38a88edfrj3483j4834834', 20); - тестовое значение
INSERT INTO validators (user_address, reputation) VALUES ('da38a88erj34fdf83j4834834', 40); - тестовое значение

SELECT user_address FROM validators WHERE reputation = (SELECT max(reputation) from validators)

Общий вид таблицы:

  '         user_address           ' 'reputation'
1 '38a88erj3483j4834834            ' '    30    '
2 'fdf38a88edfrj3483j4834834       ' '    20    '
3 'da38a88erj34fdf83j4834834       ' '    40    '

user_address - открытый ключ (идентификатор) пользователя. При регистрации для пользователя генерируется пара ключей: 
открытый и закрытый. Открытый служит идентификатором, закрытым обычно подписывают что-либо

'''