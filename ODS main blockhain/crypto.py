import rsa
import hashlib
import settings
import os


def rsa_keys():
    (PUBLIC_KEY, PRIVATE_KEY) = rsa.newkeys(settings.BYTES)

    privkey_file = open('private.pem', '+w')
    privkey_file.write(PRIVATE_KEY.save_pkcs1().decode('utf8'))
    privkey_file.close()

    pubkey_file = open('public.pem', '+w')
    pubkey_file.write(PUBLIC_KEY.save_pkcs1().decode('utf8'))
    pubkey_file.close()


def hashsum(data):
    return hashlib.sha256(str(data).encode()).hexdigest()


def verify_hash(data, hash):
    if hashlib.sha256(str(data).encode()).hexdigest() == hash:
        return True
    else:
        return False


def sign(data, private_key):
    return rsa.sign(str(data).encode(), private_key, 'SHA-256')


def verify_sign(data, sign, public_key):
    return rsa.verify(str(data).encode(), sign, public_key)


def generate_random_bytes():
    return os.urandom(settings.RAND_BYTES)


def proof_of_importance():
    pass
