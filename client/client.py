import asyncio
import websockets
import json
import diffie_hellman as dh
import os
from cryptography.hazmat.primitives import serialization
import base64

lobbyState = "lobby"
preparingOneState = "preparing_1"
preparingTwoState = "preparing_2"
chatState = "chat"

current_state = lobbyState

parameters = dh.generate_parameters()
private_key = dh.generate_private_key(parameters)
public_key = dh.generate_public_key(private_key)

number_of_participants = 0
processed_number_of_participants = 0

# First user data
participants_public_keys = {}
participants_shared_keys = {}
participants_symmetric_keys = {}
participants_salts = {}

# Non-first user data
own_symmetric_key = None
own_salt = None

KEY = None


def serialize_public_key(public_key):
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return base64.b64encode(public_bytes).decode("utf-8")


def deserialize_public_key(public_key_str):
    public_bytes = base64.b64decode(public_key_str.encode("utf-8"))
    return serialization.load_pem_public_key(public_bytes)


async def send_messages():
    global \
        participants_public_keys, \
        participants_shared_keys, \
        participants_symmetric_keys, \
        participants_salts, \
        number_of_participants, \
        processed_number_of_participants, \
        own_symmetric_key, \
        own_salt, \
        KEY

    uri = "ws://localhost:8090"
    async with websockets.connect(uri) as websocket:
        # Send identifying information upon connection
        user_info = {
            "username": "bob" + str(os.urandom(4).hex()),
            "public_key": serialize_public_key(public_key),
        }
        await websocket.send(json.dumps(user_info))

        async for message in websocket:
            data = json.loads(message)
            print(data)
            if "error" in data:
                print(data["error"])
            elif "state" in data:
                global current_state
                current_state = data["state"]
                print(f"State transitioned to: {current_state}")
                if current_state == preparingOneState:
                    number_of_participants = data["number_of_participants"]
                    await websocket.send(
                        json.dumps({"public_key": serialize_public_key(public_key)})
                    )
                elif current_state == preparingTwoState:
                    first_user_public_key = deserialize_public_key(
                        data["first_user_public_key"]
                    )
                    shared_key = dh.generate_shared_key(
                        private_key, first_user_public_key
                    )
                    own_symmetric_key, own_salt = dh.derive_key(shared_key)
                    decrypted_K = dh.decrypt_message(
                        own_symmetric_key, data["encrypted_K"]
                    )
                    KEY = decrypted_K
                    print(KEY)

            elif current_state == preparingOneState:
                # First user flow:
                participants_public_keys[data["username"]] = deserialize_public_key(
                    data["public_key"]
                )
                participants_shared_keys[data["username"]] = dh.generate_shared_key(
                    private_key, participants_public_keys[data["username"]]
                )
                (
                    participants_symmetric_keys[data["username"]],
                    participants_salts[data["username"]],
                ) = dh.derive_key(participants_shared_keys[data["username"]])
                processed_number_of_participants += 1
                if processed_number_of_participants >= number_of_participants - 1:
                    K = os.urandom(32)
                    KEY = K
                    print(KEY)
                    await websocket.send(
                        json.dumps(
                            {
                                "state": preparingTwoState,
                                "first_user_public_key": serialize_public_key(
                                    public_key
                                ),
                                "encrypted_K": {
                                    k: dh.encrypt_message(v, K)
                                    for k, v in participants_symmetric_keys.items()
                                },
                            }
                        )
                    )
            elif current_state == chatState:
                print(f"Received message: {data}")


if __name__ == "__main__":
    asyncio.run(send_messages())
