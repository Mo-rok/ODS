from flask import Flask, jsonify, request
import chain
import rsa
import json
import hashlib

app = Flask(__name__)
blockchain = chain.BlockChain()

# Идентификатор ноды: Открытый ключ -> Алгоритм хеширования N1 -> Алгоритм хеширования N2 -> Хеш открытого ключа -> Алгоритм кодировки с префиксом 0x00

with open('public.pem') as public_file:
    keydata = public_file.read()

# Читаем публичный ключ из файла
public = rsa.PublicKey.load_pkcs1(keydata)

# Хешируем публичный ключ алгоритмом SHA256 первый раз
first_hash_loop = hashlib.sha256(str(public).encode()).hexdigest()

# Хешируем хеш публичного ключа MD5 второй раз
second_hash_loop = hashlib.md5(str(first_hash_loop).encode()).hexdigest()

# Получаем идентификатор ноды
node_identified = second_hash_loop

print(node_identified)


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    if blockchain.mine(last_block) is True:
        with open('private.pem', mode='rb') as privatefile:
            keydata = privatefile.read()
        privkey = rsa.PrivateKey.load_pkcs1(keydata)

        with open('public.pem', mode='rb') as pubfile:
            keydata2 = pubfile.read()
        pubkey = rsa.PublicKey.load_pkcs1(keydata2)

        blockchain.new_transaction(
            private_key=privkey,
            public_key=pubkey,
            sender='ODS blockchain Father',
            receiver=node_identified,
            value=100
        )

        block = blockchain.new_block(privkey, pubkey, node_identified)

        print(block)
        print(type(block))

        response = {
            'message': 'New Block Forged',
            'index': block['index'],
            'timestamp': block['timestamp'],
            'transactions': block['transactions'],
            'previous_hash': block['previous_hash'],
            'miner': block['miner'],
        }

        return jsonify(json.dumps(str(response))), 200

    else:
        response = {
            'message': "New Block can't be Forged. Error"
        }

        return jsonify(response), 400


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }

    print(type(blockchain.chain))
    return jsonify(json.dumps(str(response))), 200


@app.route('/transactions/new', methods=['POST'])
def new_transactions():
    values = request.get_json(force=True)
    required = ['sender', 'receiver', 'value']

    if not all(k in values for k in required):
        return 'Missing values', 400

    with open('private.pem', mode='rb') as privatefile:
        keydata = privatefile.read()
    privkey = rsa.PrivateKey.load_pkcs1(keydata)

    with open('public.pem', mode='rb') as pubfile:
        keydata2 = pubfile.read()
    pubkey = rsa.PublicKey.load_pkcs1(keydata2)

    index = blockchain.new_transaction(privkey, pubkey, values['sender'],
                                       values['receiver'], values['value'])

    response = {'message': f'Transaction will be added to block {index}'}
    return jsonify(response), 201


# Нода не попадает в список нод блокчейна, исправить
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json(force=True)
    nodes = values.get('nodes')
    if nodes is None:
        return 'Error: Please supply a valid list of nodes', 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


@app.route('/nodes/total_nodes', methods=['GET'])
def total_nodes():
    response = {
        'message': 'All blockchain-nodes:',
        'total_nodes': list(blockchain.nodes)
    }

    return jsonify(response), 201


@app.route('/nodes/disconnect_node', methods=['POST'])
def disconncet_node():
    pass


@app.route('/nodes/set_ban', methods=['POST'])
def set_ban_node():
    pass


@app.route('/users/new', methods=['GET'])
def user_registration():
    try:
        blockchain.new_user()
        response = {'message': 'new user was created successful'}
        return jsonify(response), 201

    except:
        response = {'message': 'user creation is failed'}
        return jsonify(response), 400


@app.route('/users/get_balance', methods=['POST'])
def get_balance():
    values = request.get_json(force=True)
    required = 'address'

    if required not in values:
        return 'Error, no address', 400

    else:
        balance = blockchain.get_balance(values['address'])
        response = {'message': f'Your balance is {balance}'}
        return jsonify(response), 201

# Функция сериализации данных, заменить ею return-ы выше


def serialize(value):
    return json.dumps(str(value))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
