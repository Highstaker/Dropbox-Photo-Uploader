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

print("u.message.photo",u.message.photo)

#bot.downloadPhoto(u,custom_filepath='001.tiff')
