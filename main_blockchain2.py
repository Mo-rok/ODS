'''
1.Прикрутить Flask для обращения к методам блокчейна по HTTP
2.Реализовать регистрацию пользователей. Данные будут сохраняться с помощью MongoDB
3.Реализовать Proof-of-Importance (PoI)
'''
# Для оптимизации, лучше "точечно" импортировать конкретные модули библиотек с помощью from
from hashlib import sha256
# from time import time
# import json
from datetime import datetime
import threading
from queue import Queue, Empty
from random import choice

class ODS_blockchain():
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.My_Lock = threading.Lock()
        self.temp_blocks = []
        self.candidate_blocks = Queue()
        self.validators = {}

        self.genesis_block = {
            "Index": 0,
            'previous_hash': "",
            'timestamp': str(datetime.now()),
            'transactions': self.current_transactions,
            "Validator": "",
            'validator_reputation': 10       # Первичный блок
        }
        self.genesis_block['current_hash'] = self.calc_hash(self.genesis_block)
        print(self.genesis_block)
        self.chain.append(self.genesis_block)

        thread_canditate = threading.Thread(target=self.candidate, args=(self.candidate_blocks,), daemon=True)
        thread_pick = threading.Thread(target=self.proof_of_importance(), daemon=True)

        thread_canditate.start()
        thread_pick.start()

    def new_block(self, oldblock, address, validator_reputation, previous_hash=None):                #Процедура генерации блока
        """
            :param oldblock:
            :param address:
            :param validator_reputation:
            :param previous_hash:
            :return:
            """

        block = {                                           # Структура блока. Возможно потребуется дополнить
            "Index": oldblock["Index"] + 1,
            'previous_hash': oldblock['current_hash'],
            'timestamp': str(datetime.now()),
            'transactions': self.current_transactions,
            "Validator": address,
            'validator_reputation': validator_reputation,  # Необходимое кол-во репутации для валидации
        }

        self.current_transactions = []

        # self.chain.append(block)      !!блок аппендится в блокчейн лишь на ступени алгоритма POI, как мне кажется
        block['current_hash'] = self.calc_hash(block)
        return block

    def is_block_valid(self, block, oldblock):
        # !!проверка валидности блока путем сравнения его с прошлым. проверка идет по индексу блока и хешу
        """
        :param block:
        :param oldblock:
        :return:
        """
        if oldblock["Index"] + 1 != block["Index"]:
            return False

        if oldblock["current_hash"] != block["previous_hash"]:
            return False

        if self.calc_hash(block) != block["current_hash"]:
            return False

        return True

    def new_transactions(self, sender, recipient, amount, transaction_number): # Процедура генерации транзакции для блока
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        if transaction_number == 20:                # Если в блок было записано 20 транзакций - следующие транзакции будут записаны в новый блок.
            return self.last_block['index'] + 1     # Максимальное кол-во транзакций в одном блоке нужно каким-то образом вычислить или подобрать

    def proof_of_importance(self):
        '''
        !!не доделан, пока что больше похож на POS.
        по идее работает так:
                * Функция candidate() заносит в список temp_blocks[] блоки-кандидаты на подтверждение
                * Далее из этих кандидатов вытаскивается информация об их Валидаторах
                и заносится в отдельный пул lottery_pool
                * Победитель "лотереи" находится методом choice, иначе -- выбирается рандомно
                * Блок победителя аппендится в блокчейн
        Можно бы(нужно бы) сделать так, чтобы победитель выбирался на основе:
                                        вероятность по формуле "Монеты в кошельке Валидатора / Все монеты в обиходе"
                                        +
                                        кол-во совершенных транзакций
                                        +
                                        активность нахождения в сети(только как бы превратить этот параметр в число?
                                                                                     или учитывать его другим способом)
        '''
        while True:
            with self.My_Lock:
                temp = self.temp_blocks

            lottery_pool = []

            if temp:
                for block in temp:
                    if block["Validator"] not in lottery_pool:
                        set_validators = self.validators
                        k = set_validators.get(block["Validator"])
                        if k:
                            for i in range(int(k)):
                                lottery_pool.append(block["Validator"])

                lottery_winner = choice(lottery_pool)
                print(lottery_winner)
                # добавить блок в блокчейн и дать всем знать, что он добавился и кем
                for block in temp:
                    if block["Validator"] == lottery_winner:
                        with self.My_Lock:
                            self.chain.append(block)

                        # пишет сообщение
                        msg = "\n{0} победитель\n".format(lottery_winner)
                        print(msg)

                        break

            with self.My_Lock:
                self.temp_blocks.clear()

    def candidate(self, candidate_blocks):
        """
        :param candidate_blocks:
        :return:
        """
        while True:
            try:
                candi = candidate_blocks.get(block=False)
            except Empty:
                continue
            self.temp_blocks.append(candi)

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def calc_hash(block):
        record = "".join([
            str(block["Index"]),
            str(block['previous_hash']),
            block['timestamp'],
            str(block['transactions']),
            str(block["Validator"]),
            str(block['validator_reputation']),
        ])
        return sha256(record.encode()).hexdigest()


if __name__ == '__main__':
    ODS_blockchain()
