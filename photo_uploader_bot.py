#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
from datetime import datetime
import dropbox
from random import getrandbits
from os import path
from languagesupport import LanguageSupport
from telegramHigh import telegramHigh
from subscribers import SubscribersHandler

VERSION_NUMBER = (0, 2, 1)

###############
#####PARAMS#########
###############

INITIAL_SUBSCRIBER_PARAMS = {"lang":"EN", #bot's langauge
"folder_token" : "" #a unique token generated for each user. Is used for a dropbox folder name for that user.
}

HELP_BUTTON = {"EN" : "⁉️" + "Help", "RU": "⁉️" + "Помощь"}
ABOUT_BUTTON = {"EN" : "ℹ️ About", "RU": "ℹ️ О программе"}
OTHER_BOTS_BUTTON = {"EN":"👾 My other bots", "RU": "👾 Другие мои боты"}
EN_LANG_BUTTON = "Bot language:🇬🇧 EN"
RU_LANG_BUTTON = "Язык бота:🇷🇺 RU"

START_MESSAGE = "Welcome! Type /help to get help."
HELP_MESSAGE = {"EN" : "Help message", "RU": "Файл помощи"}
ABOUT_MESSAGE = "2"
OTHER_BOTS_MESSAGE = "3"

MAIN_MENU_KEY_MARKUP = [
[HELP_BUTTON,ABOUT_BUTTON,OTHER_BOTS_BUTTON]
,[EN_LANG_BUTTON,RU_LANG_BUTTON]
]

#################
#######GLOBALS###
#################

DB_TOKEN_FILENAME = "DB_token"
with open(path.join(path.dirname(path.realpath(__file__)), DB_TOKEN_FILENAME),'r') as f:
	DB_TOKEN = f.read().replace("\n", "")

BOT_TOKEN_FILENAME = "bot_token"
with open(path.join(path.dirname(path.realpath(__file__)), BOT_TOKEN_FILENAME),'r') as f:
	BOT_TOKEN = f.read().replace("\n","")

##################
######MAIN CLASS##
##################

class UploaderBot(object):
	"""docstring for UploaderBot"""

	def __init__(self):
		super(UploaderBot, self).__init__()
		self.bot = telegramHigh(BOT_TOKEN)
		self.h_subscribers = SubscribersHandler("/tmp","dropbox_photo_uploader_subscribers.save",INITIAL_SUBSCRIBER_PARAMS)
		self.dbx = dropbox.Dropbox(DB_TOKEN)
		
	def start(self):
		while True:
			try:
				self.bot.echo(processingFunction=self.processUpdate)
			except KeyboardInterrupt:
				print("Terminated by user!")
				break

	def assignBotLanguage(self,chat_id,language):
		"""
		Assigns bot language to a subscribers list and saves to disk
		:return: None
		"""
		self.h_subscribers.set_param(chat_id=chat_id,param="lang",value=language)

	def processUpdate(self,u):
		bot = self.bot
		Message = u.message
		message = Message.text
		chat_id = Message.chat_id
		subs = self.h_subscribers

		# try initializing user. If it exists, ignore (no forcing).
		user_folder_token = hex(getrandbits(128))[2:]
		subs.init_user(chat_id, params={"folder_token": user_folder_token})

		# language support class for convenience
		print("lang:", subs.get_param(chat_id=chat_id, param="lang"))#debug
		LS = LanguageSupport(subs.get_param(chat_id=chat_id, param="lang"))
		lS = LS.languageSupport
		MMKM = lS(MAIN_MENU_KEY_MARKUP)

		if message == "/start":
			bot.sendMessage(chat_id=chat_id
				,message=lS(START_MESSAGE)
				,key_markup=MMKM
				)
		elif message == "/help" or message == lS(HELP_BUTTON):
			bot.sendMessage(chat_id=chat_id
				,message=lS(HELP_MESSAGE)
				,key_markup=MMKM
				)
		elif message == "/about" or message == lS(ABOUT_BUTTON):
			bot.sendMessage(chat_id=chat_id
				,message=lS(ABOUT_MESSAGE)
				,key_markup=MMKM
				)
		elif message == "/otherbots" or message == lS(OTHER_BOTS_BUTTON):
			bot.sendMessage(chat_id=chat_id
				,message=lS(OTHER_BOTS_MESSAGE)
				,key_markup=MMKM
				)
		elif message == RU_LANG_BUTTON:
			self.assignBotLanguage(chat_id,'RU')
			LS = LanguageSupport(subs.get_param(chat_id=chat_id, param="lang"))
			key_markup=LS.languageSupport(message=MAIN_MENU_KEY_MARKUP)
			bot.sendMessage(chat_id=chat_id
				,message="Сообщения бота будут отображаться на русском языке."
				,key_markup=key_markup
				)
		elif message == EN_LANG_BUTTON:
			self.assignBotLanguage(chat_id,'EN')
			LS = LanguageSupport(subs.get_param(chat_id=chat_id, param="lang"))
			key_markup=LS.languageSupport(message=MAIN_MENU_KEY_MARKUP)
			bot.sendMessage(chat_id=chat_id
				,message="Bot messages will be shown in English."
				,key_markup=key_markup
				)
		elif Message.photo:
			# process photo

			# get a hex-created folder name
			DB_folder_name = subs.get_param(chat_id,"folder_token")
			# name a file with a datestamp
			file_name = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
			# create a full filepath without extension
			custom_filepath = path.join("/tmp",DB_folder_name,file_name)
			# download photo to temporary folder. Save a path to the file (this one has extension)
			file_ext = bot.downloadPhoto(u,custom_filepath=custom_filepath)

			# upload to dropbox
			self.dbx.files_upload(
					open(custom_filepath+file_ext, 'rb')  # open file
					,"/" + DB_folder_name + "/" + path.basename(custom_filepath) + file_ext  # set path in dropbox
					,autorename=True
			)
		else:
			bot.sendMessage(chat_id=chat_id
				,message="Unknown command!"
				,key_markup=MMKM
				)


	# def echo(self):
	# 	bot = self.bot

	# 	upd = bot.getUpdates()

	# 	for u in upd:
	# 		self.processUpdate(upd)

def main():
	bot = UploaderBot()
	bot.start()

if __name__ == '__main__':
	main()