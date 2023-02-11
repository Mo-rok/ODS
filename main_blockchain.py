'''
1.Прикрутить Flask для обращения к методам блокчейна по HTTP
2.Реализовать регистрацию пользователей. Данные будут сохраняться с помощью MongoDB
3.Реализовать Proof-of-Importance (PoI)
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
        
    @property
    def last_block(self):
        return self.chain[-1]
 
    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()    
        

        
