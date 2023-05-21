from time import time
from urllib.parse import urlparse
import crypto
import requests


class BlockChain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        self.genesis_block = {
            'index': 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'miner': 'None',
            'nonce': 100,

        }

        self.genesis_block['current_hash'] = crypto.hashsum(self.genesis_block)
        self.chain.append(self.genesis_block)

    @staticmethod
    def new_user():
        crypto.rsa_keys()

    def new_transaction(self, private_key, public_key, sender, receiver, value):
        transaction = {
            'random_bytes': crypto.generate_random_bytes(),
            'previous_block': self.chain[-1],
            'sender': sender,
            'receiver': receiver,
            'value': value,
        }

        transaction['current_hash'] = crypto.hashsum(transaction)
        transaction['sign'] = crypto.sign(transaction, private_key)

        if transaction['value'] == 0:
            print('Error, value = 0')
            return False

        # if transaction['random_bytes'] ==

        if crypto.verify_sign(transaction, crypto.sign(transaction, private_key), public_key) is False:
            print('Error, sign is not valid')
            return False

        if crypto.verify_hash(transaction, crypto.hashsum(transaction)) is False:
            print('Error, transaction hash is not valid')
            return False

        self.current_transactions.append(transaction)

        return self.last_block['index'] + 1

    def new_block(self, private_key, public_key, miner):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'previous_hash': crypto.hashsum((self.chain[-1])),
            'miner': miner,
        }

        block['current_hash'] = crypto.hashsum(block)
        block['sign'] = crypto.sign(block, private_key)

        if block['index'] != len(self.chain) + 1:
            print('Block index is invalid')
            return False

        if crypto.verify_sign(block, crypto.sign(block, private_key), public_key) is False:
            print('Block sign is invalid')
            return False

        if crypto.verify_hash(block, crypto.hashsum(block)) is False:
            print('Block hash is invalid')
            return False

        # Перезагрузка текущего списка транзакций
        self.current_transactions = []

        self.chain.append(block)
        return block

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    @property
    def last_block(self):
        return self.chain[-1]

    def get_balance(self, address):
        summ = 0
        subs = 0
        for block in self.chain:
            for transaction in block['transactions']:
                if address == transaction['receiver']:
                    summ = summ + transaction['value']

        for block in self.chain:
            for transaction in block['transactions']:
                if address == transaction['sender']:
                    subs = subs + transaction['value']

        result = summ - subs

        return result

    def mine(self, last_block):
        return True

    def valid_chain(self, chain):
        """
        Проверяем, является ли внесенный в блок хеш корректным

        :param chain: <list> blockchain
        :return: <bool> True если она действительна, False, если нет
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Проверьте правильность хеша блока
            if block['previous_hash'] != crypto.hashsum(last_block):
                return False

            # Проверяем, является ли подтверждение работы корректным
            # if not self.valid_proof(last_block['proof'], block['proof']):
            #    return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Это наш алгоритм Консенсуса, он разрешает конфликты,
        заменяя нашу цепь на самую длинную в цепи

        :return: <bool> True, если бы наша цепь была заменена, False, если нет.
        """

        neighbours = self.nodes
        new_chain = None

        # Ищем только цепи, длиннее нашей
        max_length = len(self.chain)

        # Захватываем и проверяем все цепи из всех узлов сети
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Проверяем, является ли длина самой длинной, а цепь - валидной
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Заменяем нашу цепь, если найдем другую валидную и более длинную
        if new_chain:
            self.chain = new_chain
            return True

        return False
