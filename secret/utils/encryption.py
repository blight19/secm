from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
from django.conf import settings
import os

if settings.DEBUG:
    #debug模式 直接从settings读取

    key=settings.AES_KEY.encode('utf-8')
else:
    #正式环境从环境变量读取
    key=os.getenv('AES_KEY').encode('utf-8')


def add_to_16(text):
    if len(text.encode('utf-8')) % 16:
        add = 16 - (len(text.encode('utf-8')) % 16)
    else:
        add = 0
    text = text + ('\0' * add)
    return text.encode('utf-8')


# 加密函数
def encrypt(text):

    mode = AES.MODE_ECB
    text = add_to_16(text)
    cryptos = AES.new(key, mode)

    cipher_text = cryptos.encrypt(text)
    return b2a_hex(cipher_text)


# 解密后，去掉补足的空格用strip() 去掉
def decrypt(text):
    mode = AES.MODE_ECB
    cryptor = AES.new(key, mode)
    plain_text = cryptor.decrypt(a2b_hex(text))
    return bytes.decode(plain_text).rstrip('\0')


