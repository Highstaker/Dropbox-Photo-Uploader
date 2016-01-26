#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import telegram
from os import path

BOT_TOKEN_FILENAME = "bot_token"
with open(path.join(path.dirname(path.realpath(__file__)), BOT_TOKEN_FILENAME),'r') as f:
	BOT_TOKEN = f.read().replace("\n","")

LAST_UPDATE_ID = None

bot = telegram.Bot(BOT_TOKEN)

u = bot.getUpdates(offset=LAST_UPDATE_ID)

while u:

	u = bot.getUpdates(offset=LAST_UPDATE_ID)

	for i in u:
		LAST_UPDATE_ID = i.update_id + 1
