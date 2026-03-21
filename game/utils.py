from base64 import b64encode, b64decode
from secrets import token_hex
from typing import Any
from msgpack import packb
from msgpack.fallback import unpackb
from Crypto.Cipher import PKCS1_v1_5, AES
from Crypto.Cipher._mode_cbc import CbcMode
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


# 随机生成16字节
def createkey() -> bytes:
    return token_hex(16).encode()


# 不足16字节倍数时填充，缺N则填充N个字节‘N’
def add_to_16(b: bytes) -> bytes:
    n = len(b) % 16
    n = n // 16 * 16 - n + 16
    return b + (n * bytes([n]))


# IV 固定值
def crypt_iv() -> bytes:
    return b"7Fk9Lm3Np8Qr4Sv2"


# 创建AES-CBC加密器
def crypt_aes(key: bytes) -> CbcMode:
    return AES.new(key, AES.MODE_CBC, crypt_iv())


# 通过密钥加密
def encrypt(data: str, key: bytes) -> bytes:
    aes = crypt_aes(key)
    encode_data = add_to_16(data.encode("utf8"))
    return aes.encrypt(encode_data) + key


# 通过密钥解密
def decrypt(data: bytes) -> tuple[bytes, bytes]:
    data = b64decode(data.decode("utf8"))
    aes = crypt_aes(data[-32:])
    return aes.decrypt(data[:-32]), data[-32:]


# 通过密钥打包
def pack(data: object, key: bytes) -> bytes:
    aes = crypt_aes(key)
    encode_data = packb(data, use_bin_type=False) or b""
    encode_data = add_to_16(encode_data)
    return aes.encrypt(encode_data) + key


# 通过密钥解包
def unpack(data: bytes) -> tuple[Any, bytes]:
    data = b64decode(data.decode("utf8"))
    aes = crypt_aes(data[-32:])
    dec = aes.decrypt(data[:-32])
    return unpackb(dec[: -dec[-1]], strict_map_key=False), data[-32:]
