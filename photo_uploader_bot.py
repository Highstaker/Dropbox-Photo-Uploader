#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import os
from datetime import datetime
from queue import Queue
from threading import Thread
from time import sleep
import dropbox
from random import getrandbits
from os import path
from languagesupport import LanguageSupport
from telegramHigh import telegramHigh
from subscribers import SubscribersHandler
from list_threaded_saver import ListThreadedSaver

VERSION_NUMBER = (0, 4, 1)

# The folder containing the script itself
SCRIPT_FOLDER = path.dirname(path.realpath(__file__))

###############
#####PARAMS#########
###############

INITIAL_SUBSCRIBER_PARAMS = {"lang":"EN"  # bot's langauge
,"folder_token" : ""  # a unique token generated for each user. Is used for a dropbox folder name for that user.
}

#############
####TEXTS####
############

HELP_BUTTON = {"EN" : "⁉️" + "Help", "RU": "⁉️" + "Помощь"}
ABOUT_BUTTON = {"EN" : "ℹ️ About", "RU": "ℹ️ О программе"}
OTHER_BOTS_BUTTON = {"EN":"👾 My other bots", "RU": "👾 Другие мои боты"}
DB_STORAGE_LINK_BUTTON = {"EN": "Get Link to photos", "RU": "Ссылка на фоты"}
EN_LANG_BUTTON = "Bot language:🇬🇧 EN"
RU_LANG_BUTTON = "Язык бота:🇷🇺 RU"

START_MESSAGE = "Welcome! Type /help to get help."
HELP_MESSAGE = {"EN" : "Help message", "RU": "Файл помощи"}
DB_STORAGE_LINK_MESSAGE = {"EN": """The link to the photo storage: %s
Your folder is %s
"""
}
ABOUT_MESSAGE = "2"
OTHER_BOTS_MESSAGE = "3"

MAIN_MENU_KEY_MARKUP = [
[DB_STORAGE_LINK_BUTTON],
[HELP_BUTTON,ABOUT_BUTTON,OTHER_BOTS_BUTTON],
[EN_LANG_BUTTON,RU_LANG_BUTTON]
]

#################
#######GLOBALS###
#################

QUEUE_PARAMS_STORAGE_FILENAME = "QueueParamsStorage.save"

DB_TOKEN_FILENAME = "DB_token"
if path.isfile(DB_TOKEN_FILENAME):
	with open(path.join(SCRIPT_FOLDER, DB_TOKEN_FILENAME),'r') as f:
		DB_TOKEN = f.read().replace("\n", "")
else:
	print(DB_TOKEN_FILENAME + " doesn't exist! Create it, please!")
	quit()

BOT_TOKEN_FILENAME = "bot_token"
if path.isfile(BOT_TOKEN_FILENAME):
	with open(path.join(SCRIPT_FOLDER, BOT_TOKEN_FILENAME),'r') as f:
		BOT_TOKEN = f.read().replace("\n","")
else:
	print(BOT_TOKEN_FILENAME + " doesn't exist! Create it, please!")
	quit()

DB_STORAGE_LINK_FILENAME = "DB_shared_folder"
if path.isfile(DB_STORAGE_LINK_FILENAME):
	with open(path.join(SCRIPT_FOLDER, DB_STORAGE_LINK_FILENAME),'r') as f:
		DB_STORAGE_PUBLIC_LINK = f.read().replace("\n","")
else:
	print(DB_STORAGE_LINK_FILENAME + " doesn't exist! Create it, please!")
	quit()

##################
######MAIN CLASS##
##################

class UploaderBot(object):
	"""docstring for UploaderBot"""

	photoDownloadUpload_Daemon_process = None

	def __init__(self):
		super(UploaderBot, self).__init__()
		self.bot = telegramHigh(BOT_TOKEN)
		self.h_subscribers = SubscribersHandler(
				path.join(SCRIPT_FOLDER, "dropbox_photo_uploader_subscribers.save"),
												INITIAL_SUBSCRIBER_PARAMS)
		self.dbx = dropbox.Dropbox(DB_TOKEN)
		self.thread_keep_alive_flag = True  # a flag. When false, the sender thread terminates

		self.uploader_queue = Queue()
		# contains all parameters to be queued to thread that haven't been processed yet.
		self.queue_saver = ListThreadedSaver(filename=path.join(SCRIPT_FOLDER,QUEUE_PARAMS_STORAGE_FILENAME))

		#reload queue
		for param in self.queue_saver.list_generator():
			self.uploader_queue.put(param)

		#starts the main loop
		self.bot.start(processingFunction=self.processUpdate,
					periodicFunction=self.periodicFunction,
					   termination_function=self.termination_function
					   )

	def periodicFunction(self):
		self.launch_photoDownloadUpload_Daemon()

	def termination_function(self):
		self.thread_keep_alive_flag = False

	def launch_photoDownloadUpload_Daemon(self):
		def launch_thread():
			self.photoDownloadUpload_Daemon_process = t = Thread(target=self.photoDownloadUpload_Daemon,
															 args=(self.uploader_queue,)
															 )
			t.start()

		try:
			if not self.photoDownloadUpload_Daemon_process.isAlive:
				# if the thread is suddenly dead - restart it
				launch_thread()
		except AttributeError:
			# in the beginning there is no variable with process. Create it.
			launch_thread()

	def photoDownloadUpload_Daemon(self, queue):
		def photoDownloadUpload(bot, u, chat_id, message_id):
			subs = self.h_subscribers
			# get a hex-created folder name
			DB_folder_name = subs.get_param(chat_id,"folder_token")
			# name a file with a datestamp
			file_name = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
			# create a full filepath without extension
			custom_filepath = path.join("/tmp",DB_folder_name,file_name)

			file_ext = ".jpg" # to avoid warning
			# download photo to temporary folder. Save a path to the file (this one has extension)
			while True:
				try:
					file_ext = bot.downloadPhoto(u,custom_filepath=custom_filepath)
					break
				except:
					sleep(5)
					pass

			full_filename = custom_filepath + file_ext

			# upload to dropbox
			while True:
				try:
					self.dbx.files_upload(
					open(full_filename, 'rb')  # open file
					,"/" + DB_folder_name + "/" + path.basename(custom_filepath) + file_ext  # set path in dropbox
					,autorename=True
					)
					break
				except:
					sleep(5)
					pass

			# confirmation message
			bot.sendMessage(chat_id=chat_id
							, message="Photo uploaded!"
							, reply_to=message_id
							)

			os.remove(full_filename)

			# remove the data about this photo and update queue file
			self.queue_saver.pop_first(save=True)

		while self.thread_keep_alive_flag:
			if not queue.empty():
				kwargs = queue.get()
				photoDownloadUpload(**kwargs)
				sleep(0.1)

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
		message_id = Message. message_id
		chat_id = Message.chat_id
		subs = self.h_subscribers

		# try initializing user. If it exists, ignore (no forcing).
		user_folder_token = hex(getrandbits(128))[2:]
		while user_folder_token in [subs.subscribers[chatid]['folder_token'] for chatid in subs.subscribers.keys()]:
			# it is highly improbable, but if suddenly the folder token is generated - try again!
			user_folder_token = hex(getrandbits(128))[2:]
		subs.init_user(chat_id, params={"folder_token": user_folder_token})

		# language support class for convenience
		LS = LanguageSupport(subs.get_param(chat_id=chat_id, param="lang"))
		lS = LS.languageSupport
		MMKM = lS(MAIN_MENU_KEY_MARKUP)

		if message == "/start":
			bot.sendMessage(chat_id=chat_id
				, message=lS(START_MESSAGE)
				, key_markup=MMKM
				)
		elif message == "/help" or message == lS(HELP_BUTTON):
			bot.sendMessage(chat_id=chat_id
				, message=lS(HELP_MESSAGE)
				, key_markup=MMKM
				)
		elif message == "/about" or message == lS(ABOUT_BUTTON):
			bot.sendMessage(chat_id=chat_id
				, message=lS(ABOUT_MESSAGE)
				, key_markup=MMKM
				)
		elif message == "/otherbots" or message == lS(OTHER_BOTS_BUTTON):
			bot.sendMessage(chat_id=chat_id
				, message=lS(OTHER_BOTS_MESSAGE)
				, key_markup=MMKM
				)
		elif message == "/dblink" or message == lS(DB_STORAGE_LINK_BUTTON):
			bot.sendMessage(chat_id=chat_id
				, message=lS(DB_STORAGE_LINK_MESSAGE)
						% (DB_STORAGE_PUBLIC_LINK, subs.get_param(chat_id=chat_id, param="folder_token"))
				, key_markup=MMKM
				)
		elif message == RU_LANG_BUTTON:
			self.assignBotLanguage(chat_id,'RU')
			LS = LanguageSupport(subs.get_param(chat_id=chat_id, param="lang"))
			key_markup=LS.languageSupport(message=MAIN_MENU_KEY_MARKUP)
			bot.sendMessage(chat_id=chat_id
				, message="Сообщения бота будут отображаться на русском языке."
				, key_markup=key_markup
				)
		elif message == EN_LANG_BUTTON:
			self.assignBotLanguage(chat_id,'EN')
			LS = LanguageSupport(subs.get_param(chat_id=chat_id, param="lang"))
			key_markup=LS.languageSupport(message=MAIN_MENU_KEY_MARKUP)
			bot.sendMessage(chat_id=chat_id
				, message="Bot messages will be shown in English."
				, key_markup=key_markup
				)
		elif Message.photo:
			# process photo
			thread_params = dict(bot=bot, u=u, chat_id=chat_id,
						 message_id=message_id,
						 )
			# save params to file
			self.queue_saver.append_to_list(thread_params, save=True)
			# send params to Queue for thread to process
			self.uploader_queue.put(thread_params)

		else:
			bot.sendMessage(chat_id=chat_id
				,message="Unknown command!"
				,key_markup=MMKM
				)


def main():
	bot = UploaderBot()

if __name__ == '__main__':
	main()