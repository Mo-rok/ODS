'''Что должен делать блокчейн? (можно дополнить): 
    1.Регистрация пользователя (для начала - запросить желаемое имя (ник) и проверить 
    свободен ли он, завести счёт для операций с криптовалютой, создание записи в блокчейне)
    2.Создание и обработка транзакций на прием и отправку криптовалюты между 
    пользователями
    
   Какая информация должа содержаться в блоке?:
   1.Время добычи блока
   2.Длина блокчейна с учетом текущего блока
   3.Идентификатор данного блока (хеш)
   4.Идентификатор предыдущего блока (хеш)
   5.Транзакции (от кого, кому, переводимый номинал)
   
   Оставшиеся вопросы:
   1.Сколько максимум транзакций будут внутри блока перед созданием нового?
   2...
'''

from hashlib import sha256              #Для оптимизации, лучше "точечно" импортировать конкретные модули библиотек с помощью from
from time import time 
import json     


class ODS_blockchain():
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.new_block(previous_hash=1, validator_reputation=10) #Первичный блок
        
    def new_block(self, validator_reputation, previous_hash=None):                #Процедура генерации блока
        block = {                                           #Структура блока. Возможно потребуется дополнить  
            'current_hash': len(self.chain) + 1,            
            'previous_hash': self.hash(self.chain[-1]),
            'timestamp': time(),
            'transactions': self.current_transactions,
            'validator_reputation': validator_reputation,   #Необходимое кол-во репутации для валидации 
        }

        self.current_transactions = []
        self.chain.append(block)
        
        return block
        
    def new_transactions(self, sender, recipient, amount, transaction_number): #Процедура генерации транзакции для блока
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        
        if transaction_number == 20:                #Если в блок было записано 20 транзакций - следующие транзакции будут записаны в новый блок.
            return self.last_block['index'] + 1     #Максимальное кол-во транзакций в одном блоке нужно каким-то образом вычислить или подобрать
     
    def proof_of_importance(self):
        pass
   
        '''Моё виденье реализации PoW - на каждый блок мы устанавливаем 
        пороговое значение репутации которое необходимо иметь ноде для 
        права валидации данного блока. У каждого последующего блока 
        значение требуемой репутации должно увеличиваться.
        
        Какие вижу проблемы на данный момент? - Необходимо откуда-то брать
        список нод, в котором помимо их идентификатора будет указано кол-во 
        их репутации. Помимо того, необходимо придумать, что делать в случае
        если две и более нод имеют одно и то же кол-во репутации?'''
        
    @property
    def last_block(self):
        return self.chain[-1]
 
    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()    
        

        