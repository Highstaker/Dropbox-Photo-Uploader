#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime
from queue import Queue
from threading import Thread
from time import sleep
import dropbox
from random import getrandbits
from os import path, listdir
from telegram import TelegramError

from infofile_thread import InfofileThread
from languagesupport import LanguageSupport
from telegramHigh import telegramHigh
from subscribers import SubscribersHandler
from list_threaded_saver import ListThreadedSaver
from tracebackprinter import full_traceback

VERSION_NUMBER = (0, 9, 4)

# The folder containing the script itself
SCRIPT_FOLDER = path.dirname(path.realpath(__file__))

###############
# PARAMS#########
###############

INITIAL_SUBSCRIBER_PARAMS = {"lang": "EN",  # bot's langauge
							"folder_token": "",	# a unique token generated for each user. Is used for a dropbox folder name for that user.
							"input_mode": 0,
							 "username": "",
							 "comment": ""
							}

ALLOW_FILES = False
MAX_FILE_SIZE = 8 * 1024 * 1024
SUPPORTED_FILE_FORMATS = ['jpg', 'jpeg', 'png', 'bmp']

#############
# TEXTS####
############

HELP_BUTTON = {"EN": "⁉️" + "Help", "RU": "⁉️" + "Помощь"}
ABOUT_BUTTON = {"EN": "ℹ️ About", "RU": "ℹ️ О программе"}
OTHER_BOTS_BUTTON = {"EN": "👾 My other bots", "RU": "👾 Другие мои боты"}
DB_STORAGE_LINK_BUTTON = {"EN": "Get Link to photos", "RU": "Ссылка на фоты"}
FREE_DB_SPACE_BUTTON = {"EN": "Get free space", "RU": "Свободное место"}
SET_USERNAME_BUTTON = {"EN": "Set username", "RU": "Имя пользователя"}
SET_COMMENT_BUTTON = {"EN": "Set comment", "RU": "Комментарий"}
TOGGLE_INFOFILE_BUTTON = {"EN": "Toggle Info File", "RU": "Вкл/Выкл информационный файл"}

EN_LANG_BUTTON = "🇬🇧 EN"
RU_LANG_BUTTON = "🇷🇺 RU"

START_MESSAGE = "Welcome! Type /help to get help."
DB_STORAGE_LINK_MESSAGE = {"EN": """The link to the photo storage: %s
Your folder is %s
""",
"RU": """Ссылка на хранилище фотографий: %s
Ваш личный каталог: %s
"""
							}

SET_USERNAME_MESSAGE = {"EN": "Type in your name to be shown in info file. Only Latin letters, numbers and common punctuation are allowed. Sorry about that.",
"RU": "Введите своё имя для информационного файла. Разрешены только латинские буквы, цифры и пунктуация. Сожалеем об этом."
}
SET_COMMENT_MESSAGE = {"EN": "Type in a comment text to be shown in info file. Only Latin letters, numbers and common punctuation are allowed. Sorry about that.",
"RU": "Введите комментарий для информационного файла. Разрешены только латинские буквы, цифры и пунктуация. Сожалеем об этом."
}

FREE_DB_SPACE_MESSAGE = {"EN": "Free space left: %.2f GB", "RU": "Осталось свободного места: %.2f Гбайт"}

ABOUT_MESSAGE = {"EN": """*Dropbox Photo Uploader Bot*
_Created by:_ Highstaker a.k.a. OmniSable.
[Source code](https://github.com/Highstaker/Dropbox-Photo-Uploader)
Version: """ + ".".join([str(i) for i in VERSION_NUMBER]) + """
[My channel, where I post development notes and update news](https://telegram.me/highstakerdev).

This bot uses the [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot) library.
"""
,"RU": """*Dropbox Photo Uploader Bot*
_Автор:_ Highstaker a.k.a. OmniSable.
По вопросам и предложениям обращайтесь в Телеграм (@OmniSable).
Исходный код [здесь](https://github.com/Highstaker/Dropbox-Photo-Uploader)
Версия: """ + ".".join([str(i) for i in VERSION_NUMBER]) + """
[Мой канал, где я объявляю о новых версиях ботов](https://telegram.me/highstakerdev).

Этот бот написан на основе библиотеки [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot).
"""
}
HELP_MESSAGE = {"EN": """This bot allows you to send photos via Telegram to the storage in Dropbox. Photos of each user are put into his/her personal folder.
"""
+
("""You may upload an image either as a _photo_ or as a _file_. """ if ALLOW_FILES else "")
+
"""
*Uploading as a photo*
In this mode photos are compressed, so they are uploaded much faster. But, due to compression photos lose some quality, along with their original filenames and metadata.
"""
+
("""
*Uploading as a file*
File upload allows you to save picture as-is, preserving its full quality, filename and metadata. Note that most modern cameras take photos several megabytes large. Uploading many photos in file mode is slow and also increases load on storage and bot. *Please, don't abuse!*
Currently, the maximum size of a photo is {:.1f} MB.
Accepted file formats are: {}""".format(MAX_FILE_SIZE/1024**2,", ".join(SUPPORTED_FILE_FORMATS)) if ALLOW_FILES else "")
+
"""
*Accessing storage*
To get link to photo storage, press the `{}` button. It also displays the name of your personal folder.
To get the amount of remaining free space in storage, press the `{}` button. 
""", 
"RU": """Данный бот позволяет отправлять фотографии через Телеграм в хранилище в Dropbox. Фотографии помещаются в отдельную папку для каждого пользователя.
Вы можете загрузить картинку либо как _фотографию_, либо как _файл_. 

*Загрузка в режиме фотографии*
В этом режиме фотографии сжимаются, загрузка производится быстро. Однако, сжатие приводит к потере качества, а также изменению имени и формата файла и потере метаданных.

*Загрузка в режиме файла*
Загрузка в виде файла позволяет переслать картинку в первоначальном качестве с сохранением имени файла и метаданных. Однако, ввиду больших размеров, загрузка занимает большее время, а также увеличивает нагрузку на бота и хранилище. *Пожалуйста, используйте этот режим разумно!*
Максимальный размер файла: {:.1f} Мбайт.
Допустимые форматы: {}

*Хранилище фотографий*
Для получения ссылки на хранилище файлов нажмите кнопку `{}`. Имя вашего личного каталога также будет отображено.
Чтобы узнать количество оставшегося в хранилище свободного места, нажмите кнопку `{}`. 
"""}

OTHER_BOTS_MESSAGE = {"EN": """*My other bots*:

@multitran_bot: a Russian-Whichever dictionary with support of 9 languages. Has transcriptions for English words.

@OmniCurrencyExchangeBot: a currency converter bot supporting past rates and graphs.
"""
, "RU": """*Другие мои боты*:

@multitran_bot: Русско-любой словарь с поддержкой 9 языков. Есть транскрипции английских слов.

@OmniCurrencyExchangeBot: Конвертер валют с поддержкой графиков и прошлых курсов.
"""
}

WRONG_FILE_FORMAT_MESSAGE = {"EN": "Wrong file format. Supported formats are: {0}",
"RU": "Неверный формат файла. Поддерживаемые форматы: {0}"
}

FILE_TOO_BIG_MESSAGE = {"EN": "File is too big. Maximum size is {:.1f} MB",
"RU": "Файл слишком большой. Максимальный размер файла: {:.1f} MB"
}

FILES_NOT_ALLOWED_MESSAGE = {"EN": "Sending pictures as files is not allowed. Please send them as photos.",
"RU": "Отправлять файлы не разрешено. Пожалуйста, отправьте изображения в виде фотографий."
}

MAIN_MENU_KEY_MARKUP = [
	[DB_STORAGE_LINK_BUTTON, FREE_DB_SPACE_BUTTON, SET_USERNAME_BUTTON, SET_COMMENT_BUTTON, TOGGLE_INFOFILE_BUTTON],
	[HELP_BUTTON, ABOUT_BUTTON, OTHER_BOTS_BUTTON],
	[EN_LANG_BUTTON, RU_LANG_BUTTON]
]

#################
# GLOBALS###
#################

QUEUE_PARAMS_STORAGE_FILENAME = "QueueParamsStorage.save"

DB_TOKEN_FILENAME = "DB_token"
if path.isfile(path.join(SCRIPT_FOLDER, DB_TOKEN_FILENAME)):
	with open(path.join(SCRIPT_FOLDER, DB_TOKEN_FILENAME), 'r') as f:
		DB_TOKEN = f.read().replace("\n", "")
else:
	print(DB_TOKEN_FILENAME + " doesn't exist! Create it, please!")
	quit()

BOT_TOKEN_FILENAME = "bot_token"
if path.isfile(path.join(SCRIPT_FOLDER, BOT_TOKEN_FILENAME)):
	with open(path.join(SCRIPT_FOLDER, BOT_TOKEN_FILENAME), 'r') as f:
		BOT_TOKEN = f.read().replace("\n", "")
else:
	print(BOT_TOKEN_FILENAME + " doesn't exist! Create it, please!")
	quit()

DB_STORAGE_LINK_FILENAME = "DB_shared_folder"
if path.isfile(path.join(SCRIPT_FOLDER, DB_STORAGE_LINK_FILENAME)):
	with open(path.join(SCRIPT_FOLDER, DB_STORAGE_LINK_FILENAME), 'r') as f:
		DB_STORAGE_PUBLIC_LINK = f.read().replace("\n", "")
else:
	print(DB_STORAGE_LINK_FILENAME + " doesn't exist! Create it, please!")
	quit()


##################
# MAIN CLASS##
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
		self.queue_saver = ListThreadedSaver(filename=path.join(SCRIPT_FOLDER, QUEUE_PARAMS_STORAGE_FILENAME))

		# reload queue
		for param in self.queue_saver.list_generator():
			self.uploader_queue.put(param)

		# starts the main loop
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

		return free_space / 1024 ** UNITS[units]

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
			print("Queue size", queue.qsize())  # debug

			subs = self.h_subscribers

			# get a hex-created folder name
			DB_folder_name = subs.get_param(chat_id, "folder_token")

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
			full_filepath = path.join("/tmp", DB_folder_name, full_filename)
			# full path without file name
			full_dir_path = path.dirname(full_filepath)

			# download photo to temporary folder.
			while True:
				try:
					bot.downloadFile(bot.getFileID(update), custom_filepath=full_filepath)
					break
				except Exception:
					logging.error("Could not download photo, retrying. Traceback:\n" + full_traceback())
					sleep(5)
					pass

			# change to file's dir
			os.chdir(full_dir_path)

			# sometimes a file is downloaded with a different name. verify that it exists and renme if the name is wrong
			if not path.isfile(full_filepath):
				# list of files in a directory
				onlyfiles = [fle for fle in listdir(full_dir_path) if path.isfile(fle)]
				# Get the latest file in the directory
				wrong_file = max(onlyfiles, key=path.getctime)
				# Rename it
				os.rename(wrong_file, full_filename)

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
				except Exception:
					logging.error("Could not upload to Dropbox, retrying. Traceback:\n" + full_traceback())
					sleep(5)

			# confirmation message
			bot.sendMessage(chat_id=chat_id, message="Photo uploaded!", reply_to=message_id)

			# remove all files from temp folder
			for i in listdir(full_dir_path):
				os.remove(i)

			# remove the data about this photo and update queue file
			self.queue_saver.pop_first(save=True)

		# keep the thread running until the main thread signals to quit
		while self.thread_keep_alive_flag:
			# launch processing routine only if there is something to process
			if not queue.empty():
				kwargs = queue.get()
				photoDownloadUpload(**kwargs)
			sleep(0.1)

	def assignBotLanguage(self, chat_id, language):
		"""
		Assigns bot language to a subscribers list and saves to disk
		:param language:
		:param chat_id:
		:return: None
		"""
		self.h_subscribers.set_param(chat_id=chat_id, param="lang", value=language)

	def processUpdate(self, u):
		def sendParamsToThread(**kwargs):
			# process photo
			thread_params = dict(bot=bot, update=u, chat_id=chat_id, message_id=message_id)
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
							, message=lS(HELP_MESSAGE).format(lS(DB_STORAGE_LINK_BUTTON), lS(FREE_DB_SPACE_BUTTON))
							, key_markup=MMKM
							, markdown=True
							)
		elif message == "/about" or message == lS(ABOUT_BUTTON):
			bot.sendMessage(chat_id=chat_id
							, message=lS(ABOUT_MESSAGE)
							, key_markup=MMKM
							, markdown=True
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
							, preview=False
							)
		elif message == "/free" or message == lS(FREE_DB_SPACE_BUTTON):
			bot.sendMessage(chat_id=chat_id
							, message=lS(FREE_DB_SPACE_MESSAGE) % self.get_free_dbx_space()
							, key_markup=MMKM
							)
		elif message == "/set_name" or message == lS(SET_USERNAME_BUTTON):
			subs.set_param(chat_id=chat_id,param="input_mode", value=1)
			bot.sendMessage(chat_id=chat_id
							, message=lS(SET_USERNAME_MESSAGE)
							, key_markup=MMKM
							)
		elif message == "/set_comment" or message == lS(SET_COMMENT_BUTTON):
			subs.set_param(chat_id=chat_id,param="input_mode", value=2)
			bot.sendMessage(chat_id=chat_id
							, message=lS(SET_COMMENT_MESSAGE)
							, key_markup=MMKM
							)
		elif message == "/toggle_infofile" or message == lS(TOGGLE_INFOFILE_BUTTON):
			InfofileThread(bot, self.dbx, chat_id, subs.get_param(chat_id, "folder_token"),
						subs.get_param(chat_id, "username"), subs.get_param(chat_id, "comment"),
						subs.get_param(chat_id, "lang"))
		elif message == RU_LANG_BUTTON:
			self.assignBotLanguage(chat_id, 'RU')
			LS = LanguageSupport(subs.get_param(chat_id=chat_id, param="lang"))
			key_markup = LS.languageSupport(message=MAIN_MENU_KEY_MARKUP)
			bot.sendMessage(chat_id=chat_id
							, message="Сообщения бота будут отображаться на русском языке."
							, key_markup=key_markup
							)
		elif message == EN_LANG_BUTTON:
			self.assignBotLanguage(chat_id, 'EN')
			LS = LanguageSupport(subs.get_param(chat_id=chat_id, param="lang"))
			key_markup = LS.languageSupport(message=MAIN_MENU_KEY_MARKUP)
			bot.sendMessage(chat_id=chat_id
							, message="Bot messages will be shown in English."
							, key_markup=key_markup
							)
		elif bot.isPhoto(u):
			print("Sending params to thread on message. photo")  # debug
			sendParamsToThread(bot=bot, update=u, chat_id=chat_id, message_id=message_id)
		elif bot.isDocument(u):
			if ALLOW_FILES:
				try:
					# check supported file formats
					if not (bot.getFileExt(u, no_dot=True).lower() in SUPPORTED_FILE_FORMATS):
						bot.sendMessage(chat_id=chat_id
										, message=lS(WRONG_FILE_FORMAT_MESSAGE).format(", ".join(
										SUPPORTED_FILE_FORMATS))
										, reply_to=message_id
										)
					# limit filesize
					elif bot.getFileSize(u) > MAX_FILE_SIZE:
						bot.sendMessage(chat_id=chat_id
										, message=lS(FILE_TOO_BIG_MESSAGE).format(MAX_FILE_SIZE / 1024 ** 2)
										, reply_to=message_id
										)
					else:
						print("Sending params to thread on message. Document")  # debug
						sendParamsToThread(bot=bot, update=u, chat_id=chat_id, message_id=message_id)
				except TelegramError:
					logging.error("Could not process file.\n" + full_traceback())
					bot.sendMessage(chat_id=chat_id
									, message="Failed to process file"
									, reply_to=message_id
									)
			else:
				bot.sendMessage(chat_id=chat_id
						, message=lS(FILES_NOT_ALLOWED_MESSAGE)
						, reply_to=message_id
						)
		else:
			if subs.get_param(chat_id,"input_mode") == 1:
				# Username input mode
				subs.set_param(chat_id, param="username", value=message)
				subs.set_param(chat_id, param="input_mode", value=0)
				bot.sendMessage(chat_id=chat_id
								, message="Username set!"
								, key_markup=MMKM
								)
				InfofileThread(bot, self.dbx, chat_id, subs.get_param(chat_id, "folder_token"),
					subs.get_param(chat_id, "username"), subs.get_param(chat_id, "comment"),
					subs.get_param(chat_id, "lang"), recreate=True)
			elif subs.get_param(chat_id,"input_mode") == 2:
				# Comment input mode
				subs.set_param(chat_id, param="comment", value=message)
				subs.set_param(chat_id, param="input_mode", value=0)
				bot.sendMessage(chat_id=chat_id
								, message="Comment set!"
								, key_markup=MMKM
								)
				InfofileThread(bot, self.dbx, chat_id, subs.get_param(chat_id, "folder_token"),
					subs.get_param(chat_id, "username"), subs.get_param(chat_id, "comment"),
					subs.get_param(chat_id, "lang"), recreate=True)
			else:
				bot.sendMessage(chat_id=chat_id
								, message="Unknown command!"
								, key_markup=MMKM
								)


def main():
	bot = UploaderBot()


if __name__ == '__main__':
	main()
