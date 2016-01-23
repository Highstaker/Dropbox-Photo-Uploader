#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import logging
import telegram
from os import path, makedirs
from random import getrandbits

from telegramHigh import telegramHigh

BOT_TOKEN_FILENAME = "bot_token"
with open(path.join(path.dirname(path.realpath(__file__)), BOT_TOKEN_FILENAME),'r') as f:
	BOT_TOKEN = f.read().replace("\n","")

bot = telegramHigh(BOT_TOKEN)

u = bot.getUpdates()[-1]

chat_id = u.message.chat_id

print("u.message.document",u.message.document)
print("u.message.document.file_size",u.message.document.file_size)

File = bot.bot.getFile(u.message.document['file_id'])
print("File ",File)
print("File size ",File["file_size"])

print("bot.getFileExt(u)",bot.getFileExt(u,no_dot=True).lower())

# bot.downloadDocument(u,custom_filepath='/tmp/001')
