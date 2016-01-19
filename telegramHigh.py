#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

# Questions:
# +Should breakLongMessage() be made static?
# +Is there a better way to avoid dummyFunction?
# +Should I put MAX_CHARS_PER_MESSAGE as a static variable of telegramHigh class?
# +Better ways of printing errors with lines.

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
											 reply_markup=(telegram.ReplyKeyboardMarkup(
													 key_markup) if key_markup != "SAME" else None) if key_markup else telegram.ReplyKeyboardHide()
											 , reply_to_message_id=reply_to
											 )
				except Exception as e:
					if "Message is too long" in str(e):
						self.sendMessage(chat_id=chat_id
										 , message="Error: Message is too long!"
										 )
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
				logging.error(
						"Could not read updates. Retrying! Error: " + str(sys.exc_info()[-1].tb_lineno) + ": " + str(e))
				sleep(1)
				continue
			break
		return updates

	def downloadPhoto(self, u, custom_filepath=None):
		"""
		Downloads a photo in a given update, if there is any.
		:param custom_filepath: a path where the photo should be saved.
		File extension is ignored as it is assigned based on file extension of picture in the received message.
		If None, it will be saved to current folder, and a name is given based on filename in message metadata.
		:param u: an update from getUpdates()
		:return: file extension
		"""
		file_ext = ""
		if u.message.photo:
			# there are several photos in one message. The last one in the list is the one with highest resolution
			file_id = u.message.photo[-1]['file_id']
			# getting a file by its ID
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
		else:
			logging.warning("No photo in this message", str(u))
		return file_ext

	def echo(self, processingFunction=dummyFunction, periodicFunction=dummyFunction):
		bot = self.bot

		periodicFunction()

		updates = self.getUpdates()

		# main message processing routine
		for update in updates:
			logging.warning("Received message: " + str(
					update.message.chat_id) + " " + update.message.from_user.username + " " + update.message.text)

			processingFunction(update)

			# Updates global offset to get the new updates
			self.LAST_UPDATE_ID = update.update_id + 1
