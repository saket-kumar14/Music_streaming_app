from Crypto.Cipher import AES

from datetime import datetime

def validateToken(token, nonce, tag):
    try:
        # Check if token is a string
        if type(token) != str:
            print("[ERROR]: Token is not a string!")
            return -1
        
        # Read key from file
        f = open("./middleware/key/aes_key", "rb")
        key = f.read()
        f.close()

        # Generate cipher
        cipher = AES.new(key, AES.MODE_EAX, nonce=bytes.fromhex(nonce))

        # Decrypt token
        decryptedToken = cipher.decrypt_and_verify(bytes.fromhex(token), bytes.fromhex(tag)).decode('utf-8')

        decryptedToken = eval(decryptedToken)

        # Check if token is expired
        if datetime.strptime(decryptedToken['expires_at'], "%d-%m-%Y %H:%M:%S") < datetime.now():
            print("[ERROR]: Token is expired!")
            return -2

        return decryptedToken
    except Exception as e:
        print(e)
        print("[ERROR]: Could not validate token!")
        return -1


# print(validateToken('d2cf672cd1fc2ff29898402bbf1a7f6b6db79db547a72c6caa809eaaf108cd06e7beedbfc18051180ad5ade90768020a1b916cf05cc5e44a6043f7', '810609f4cf7f109c39f02331213957b8', '218bc1a081e24aa5dcdf7dd5f5668a3b'))