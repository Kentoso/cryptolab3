from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import os

def generate_parameters():
    parameters = dh.generate_parameters(generator=2, key_size=512, backend=default_backend())
    return parameters

def generate_private_key(parameters):
    private_key = parameters.generate_private_key()
    return private_key

def generate_public_key(private_key):
    public_key = private_key.public_key()
    return public_key

def generate_shared_key(private_key, peer_public_key):
    shared_key = private_key.exchange(peer_public_key)
    return shared_key

def derive_key(shared_key, salt=None, length=32):
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(shared_key)
    return key, salt

if __name__ == "__main__":
    # generate common parameters
    parameters = generate_parameters()
    print(parameters)

    # user A generates their private and public keys
    private_key_A = generate_private_key(parameters)
    public_key_A = generate_public_key(private_key_A)
    print('Stage 1 - ok')

    # user B generates their private and public keys
    private_key_B = generate_private_key(parameters)
    public_key_B = generate_public_key(private_key_B)
    print('Stage 2 - ok')

    # exchange public keys and generate the shared key
    shared_key_A = generate_shared_key(private_key_A, public_key_B)
    shared_key_B = generate_shared_key(private_key_B, public_key_A)
    print('Stage 3 - ok')

    # derive the symmetric keys from the shared keys
    symmetric_key_A, salt_A = derive_key(shared_key_A)
    symmetric_key_B, salt_B = derive_key(shared_key_B, salt_A)  
    print('Stage 4 - ok')

    # both keys should be the same
    assert symmetric_key_A == symmetric_key_B
    print("Symmetric keys match and are ready for encryption.")