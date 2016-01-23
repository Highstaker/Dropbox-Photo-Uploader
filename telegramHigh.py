#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

# Questions:
# +Should breakLongMessage() be made static?
# +Is there a better way to avoid dummyFunction?
# +Should I put MAX_CHARS_PER_MESSAGE as a static variable of telegramHigh class?
# +Better ways of printing errors with lines.
# +Is it readable to put single statements on same lines as in markup function?
# +Maybe merge downloadDocument and downloadPhoto with downloadFile?
# +What should be made private? make downloadFile private?

import logging
import telegram
import socket
from os import path, makedirs
import sys
from time import sleep

# if a connection is lost and getUpdates takes too long, an error is raised
socket.setdefaulttimeout(30)

# logging settings to make them more readable and informative
logging.basicConfig(format=u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s',
					level=logging.WARNING)

############
# PARAMETERS
############

MAX_CHARS_PER_MESSAGE = 2048


##########
# METHODS
#########

def dummyFunction(*args, **kwargs):
	"""
	Does nothing, used as a placeholder
	:return: None
	"""
	pass


############
# CLASSES###
############


class telegramHigh:
	"""
	telegramHigh
	"""

	def __init__(self, token):
		super(telegramHigh, self).__init__()
		self.LAST_UPDATE_ID = None
		self.bot = telegram.Bot(token)

	@staticmethod
	def isPhoto(update):
		try:
			if update.message.photo: return True
			else: return False
		except AttributeError:
			return False

	@staticmethod
	def isDocument(update):
		try:
			if update.message.document: return True
			else: return False
		except AttributeError:
			return False

	@staticmethod
	def breakLongMessage(msg):
		"""
		Breaks a message that is too long.
		:param msg: message to be split
		:return: a list of message pieces
		"""

		# let's split the message by newlines first
		result_split = msg.split("\n")

		# the result will be stored here
		broken = []

		# splitting routine
		while result_split:
			result = ""
			while True:
				if result_split:
					result += result_split.pop(0) + "\n"
				else:
					break
				if len(result) > MAX_CHARS_PER_MESSAGE:
					break

			if result:
				n_parts = int(len(result) / MAX_CHARS_PER_MESSAGE + 1)

				for i in range(n_parts):
					broken += [result[i * len(result) // n_parts:(i + 1) * len(result) // n_parts]]

		return broken

	def sendMessage(self, chat_id, message, key_markup="SAME", preview=True, markdown=False, reply_to=None):
		"""
		Sends a text message to Telegram user
		:param chat_id: ID of chat
		:param message: text to send
		:param key_markup: a list representing a custom keyboard markup to show to user.
		If "SAME", use the same markup as before.
		If None, hide the custom keyboard.
		:param preview: Should a link in a message generate a page preview within a message?
		:param markdown: Should a message support markdown formatting?
		:param reply_to: An id of an existing message. A sent message will be a reply to that message.
		:return: None
		"""
		def markup(m):
			if not m: return telegram.ReplyKeyboardHide()
			elif m == "SAME": return None
			else: return telegram.ReplyKeyboardMarkup(m)

		logging.warning("Replying to " + str(chat_id) + ": " + message)
		fulltext = self.breakLongMessage(message)
		for text in fulltext:
			# iterating over parts of a long split message
			while True:
				try:
					if text:
						self.bot.sendChatAction(chat_id, telegram.ChatAction.TYPING)
						self.bot.sendMessage(chat_id=chat_id,
											text=text,
											parse_mode='Markdown' if markdown else None,
											disable_web_page_preview=(not preview),
											reply_markup=markup(key_markup),
											reply_to_message_id=reply_to
											)
				except Exception as e:
					if "Message is too long" in str(e):
						self.sendMessage(chat_id=chat_id, message="Error: Message is too long!")
					elif ("urlopen error" in str(e)) or ("timed out" in str(e)):
						logging.error("Could not send message. Retrying! Error: " + str(
								sys.exc_info()[-1].tb_lineno) + ": " + str(e))
						sleep(3)
						continue
					else:
						logging.error(
								"Could not send message. Error: " + str(sys.exc_info()[-1].tb_lineno) + ": " + str(e))
				break

	def sendPic(self, chat_id, pic, caption=None):
		"""
		Sends a picture in a Telegram message to a user.
		:param chat_id: ID of chat
		:param pic: a picture file. Preferably the object created with open()
		:param caption: a text that goes together with picture ina message.
		:return: None
		"""
		while True:
			try:
				logging.debug("Picture: " + str(pic))
				self.bot.sendChatAction(chat_id, telegram.ChatAction.UPLOAD_PHOTO)
				# set file read cursor to the beginning.
				# This ensures that if a file needs to be re-read (may happen due to exception), it is read from the beginning.
				pic.seek(0)
				self.bot.sendPhoto(chat_id=chat_id, photo=pic, caption=caption)
			except Exception as e:
				logging.error(
						"Could not send picture. Retrying! Error: " + str(sys.exc_info()[-1].tb_lineno) + ": " + str(e))
				sleep(1)
				continue
			break

	def getUpdates(self):
		"""
		Gets updates. Updates are basically messages sent to bot from users.
		Retries if it fails.
		:return: a list of update objects
		"""
		# if getting updates fails - retry
		updates = []
		while True:
			try:
				updates = self.bot.getUpdates(offset=self.LAST_UPDATE_ID)
			except Exception as e:
				logging.error("Could not read updates. Retrying! Error: " +
							str(sys.exc_info()[-1].tb_lineno) + ": " + str(e))
				sleep(1)
				continue
			break
		return updates

	def getFileID(self, update, photoIndex=-1):
		if self.isPhoto(update):
			file_id = update.message.photo[photoIndex]['file_id']
		elif self.isDocument(update):
			file_id = update.message.document['file_id']
		else:
			file_id = ""

		return file_id

	def getFile(self, file_id):
		return self.bot.getFile(file_id)

	def getFileExt(self, update, no_dot=False):
		"""

		:param update:
		:return:
		"""
		file_id = self.getFileID(update)

		File = self.getFile(file_id)
		pth = File.file_path
		file_ext = path.splitext(pth)[1]
		if no_dot:
			file_ext = file_ext.replace(".","")
		return file_ext

	def getFileSize(self, update):

		file_id = self.getFileID(update)

		File = self.getFile(file_id)
		file_size = File['file_size']
		return file_size

	def downloadFile(self, file_id, custom_filepath=None):
		"""

		:param file_id:
		:return:
		"""
		file_ext = ""

		File = self.bot.getFile(file_id)
		if custom_filepath:
			# finding out the extension of an image file on Telegram server
			file_name_with_path, file_ext = path.splitext(File.file_path)
			# directory path to save image to
			directory = path.dirname(custom_filepath)
			# gluing together a filepath and extension, overriding one specified in arguments
			custom_filepath = path.splitext(custom_filepath)[0] + file_ext
			# create a directory if it doesn't exist
			if directory:
				makedirs(directory, exist_ok=True)
		# download the file to a given directory
		File.download(custom_path=custom_filepath)

		return file_ext

	def start(self, processingFunction=dummyFunction, periodicFunction=dummyFunction,
			termination_function=dummyFunction, slp=0.1):
		while True:
			try:
				# a function that is called regardless of updates' presence
				periodicFunction()
				self.updateProcessing(processingFunction=processingFunction)
				sleep(slp)
			except KeyboardInterrupt:
				print("Terminated by user!")
				termination_function()

				# this ensures that LAST_UPDATE_ID is updated
				#  or else it will process already processed messages after restart
				self.getUpdates()
				break

	def updateProcessing(self, processingFunction=dummyFunction):

		# basically, messages sent to bot
		updates = self.getUpdates()

		# main message processing routine
		for update in updates:
			logging.warning("Received message: " + str(
					update.message.chat_id) + " " + update.message.from_user.username + " " + update.message.text)

			# a functions that processes updates, one by one
			processingFunction(update)

			# Updates global offset to get the new updates
			self.LAST_UPDATE_ID = update.update_id + 1
