#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import logging
import telegram
from os import path, makedirs
from random import getrandbits

BOT_TOKEN_FILENAME = "bot_token"
with open(path.join(path.dirname(path.realpath(__file__)), BOT_TOKEN_FILENAME),'r') as f:
	BOT_TOKEN = f.read().replace("\n","")

bot = telegram.Bot(BOT_TOKEN)

u = bot.getUpdates()[-1]

chat_id = u.message.chat_id

print("u.message.photo",u.message.photo)

if u.message.photo:

	file_id = u.message.photo[-1]['file_id']  # there are several photos in one message. The last one in the list is the highest resolution
	print("u.message.photo",u.message.photo[-1])
	print("file_id",file_id)

	File = bot.getFile(file_id)
	print("File",File)

	rand_dir = hex(getrandbits(128))[2:]
	makedirs(path.join('/tmp',rand_dir),exist_ok=True)
	File.download(custom_path=path.join('/tmp',rand_dir))

