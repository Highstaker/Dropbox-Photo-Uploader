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

VERSION_NUMBER = (0, 8, 0)

# The folder containing the script itself
SCRIPT_FOLDER = path.dirname(path.realpath(__file__))

###############
#####PARAMS#########
###############

INITIAL_SUBSCRIBER_PARAMS = {"lang":"EN"  # bot's langauge
,"folder_token" : ""  # a unique token generated for each user. Is used for a dropbox folder name for that user.
}

MAX_FILE_SIZE = 8*1024*1024
SUPPORTED_FILE_FORMATS = ['jpg','jpeg','png','bmp']

#############
####TEXTS####
############

HELP_BUTTON = {"EN" : "⁉️" + "Help", "RU": "⁉️" + "Помощь"}
ABOUT_BUTTON = {"EN" : "ℹ️ About", "RU": "ℹ️ О программе"}
OTHER_BOTS_BUTTON = {"EN":"👾 My other bots", "RU": "👾 Другие мои боты"}
DB_STORAGE_LINK_BUTTON = {"EN": "Get Link to photos", "RU": "Ссылка на фоты"}
FREE_DB_SPACE_BUTTON = {"EN": "Get free space", "RU": "Свободное место"}

EN_LANG_BUTTON = "Bot language:🇬🇧 EN"
RU_LANG_BUTTON = "Язык бота:🇷🇺 RU"

START_MESSAGE = "Welcome! Type /help to get help."
HELP_MESSAGE = {"EN" : "Help message", "RU": "Файл помощи"}
DB_STORAGE_LINK_MESSAGE = {"EN": """The link to the photo storage: %s
Your folder is %s
"""
}
FREE_DB_SPACE_MESSAGE = {"EN": "Free space left: %.2f GB", "RU": "Осталось свободного места: %.2f Гбайт"}


ABOUT_MESSAGE = "2"
OTHER_BOTS_MESSAGE = "3"

MAIN_MENU_KEY_MARKUP = [
[DB_STORAGE_LINK_BUTTON,FREE_DB_SPACE_BUTTON],
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

	def get_free_dbx_space(self, units="GB"):
		"""
		Returns the amount of free space left in dropbox
		:param units: Specifies the units in which to display. Can be "TB", "GB", "MB", "KB" or "bytes"
		:type units: str
		:return: amount of free space left in dropbox
		:rtype: int
		"""
		UNITS = {'TB': 4, 'GB': 3, 'MB': 2, 'KB': 1, 'bytes': 0}

		# Info object
		space_usage = self.dbx.users_get_space_usage()

		# Total space (for an individual user)
		total_allocated_space = space_usage.allocation.get_individual().allocated

		# Occupied space
		used_space = space_usage.used

		# Free space
		free_space = total_allocated_space - used_space

		return free_space/1024**UNITS[units]


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
		def photoDownloadUpload(bot, update, chat_id, message_id):
			print("Queue size",queue.qsize())#debug

			subs = self.h_subscribers

			# get a hex-created folder name
			DB_folder_name = subs.get_param(chat_id,"folder_token")

			if telegramHigh.isDocument(update):
				# for documents, preserve original filename. It already has an extension.
				full_filename = bot.getDocumentFileName(update)
			else:
				# if not a document, name a file with a datestamp. (Photo objects have weird filenames)
				file_name = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
				# get an extension
				file_ext = bot.getFileExt(update)
				# sum them to get a full file name
				full_filename = file_name + file_ext
			# create a full path to the file in a temporary folder without extension
			full_filepath = path.join("/tmp",DB_folder_name,full_filename)

			# download photo to temporary folder.
			while True:
				try:
					bot.downloadFile(bot.getFileID(update), custom_filepath=full_filepath)
					break
				except:
					sleep(5)
					pass

			# upload to dropbox
			while True:
				try:
					# WARNING: files_upload is not usable for files over 140 MB
					self.dbx.files_upload(
					open(full_filepath, 'rb'),  # open file
					"/" + DB_folder_name + "/" + full_filename,  # set path in dropbox
					autorename=True
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

			# remove the file from temp folder
			os.remove(full_filepath)

			# remove the data about this photo and update queue file
			self.queue_saver.pop_first(save=True)

		# keep the thread running until the main thread signals to quit
		while self.thread_keep_alive_flag:
			#launch processing routine only if there is something to process
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
		def sendParamsToThread(**kwargs):
			# process photo
			thread_params = dict(bot=bot, update=u, chat_id=chat_id,
						 message_id=message_id,
						 )
			# save params to file
			self.queue_saver.append_to_list(thread_params, save=True)
			# send params to Queue for thread to process
			self.uploader_queue.put(thread_params)

		bot = self.bot
		Message = u.message
		message = Message.text
		message_id = Message.message_id
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
		elif message == "/free" or message == lS(FREE_DB_SPACE_BUTTON):
			bot.sendMessage(chat_id=chat_id
				, message=lS(FREE_DB_SPACE_MESSAGE) % self.get_free_dbx_space()
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
		elif bot.isPhoto(u):
			print("Sending params to thread on message. photo")#debug
			sendParamsToThread(bot=bot, update=u, chat_id=chat_id, message_id=message_id)
		elif bot.isDocument(u):
			# check supported file formats
			if not (bot.getFileExt(u,no_dot=True).lower() in SUPPORTED_FILE_FORMATS):
				bot.sendMessage(chat_id=chat_id
				, message="Wrong file format. Supported formats are: %s" % ", ".join(SUPPORTED_FILE_FORMATS)
				, reply_to=message_id
				)
			# limit filesize
			elif bot.getFileSize(u) > MAX_FILE_SIZE:
				bot.sendMessage(chat_id=chat_id
				, message="File is too big. Maximum size is %.1f MB" % (MAX_FILE_SIZE/(1024**2))
				, reply_to=message_id
				)
			else:
				print("Sending params to thread on message. Document")#debug
				sendParamsToThread(bot=bot, update=u, chat_id=chat_id, message_id=message_id)
		else:
			bot.sendMessage(chat_id=chat_id
				,message="Unknown command!"
				,key_markup=MMKM
				)


def main():
	bot = UploaderBot()

if __name__ == '__main__':
	main()