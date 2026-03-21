from base64 import b64encode
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA


# 加密消息
def rsacreate(msg: str, key: str) -> str:
    rsakey = RSA.importKey(key)
    # 创建用于执行pkcs1_v1_5加密或解密的密码
    cipher = PKCS1_v1_5.new(rsakey)

    # 消息序列化后用密码加密
    msg_buf = msg.encode("utf-8")
    cipher_buf = cipher.encrypt(msg_buf)
    cipher_buf = b64encode(cipher_buf)

    # 已加密数据反序列化
    cipher_text = cipher_buf.decode("utf-8")
    return cipher_text
