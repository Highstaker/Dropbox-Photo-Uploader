#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import logging
import telegram
import socket
from os import path, makedirs
import sys
from time import sleep

#if a connection is lost and getUpdates takes too long, an error is raised
from languagesupport import LanguageSupport

socket.setdefaulttimeout(30)

logging.basicConfig(format = u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s', 
	level = logging.WARNING)

############
##PARAMETERS
############

MAX_CHARS_PER_MESSAGE=2048

##########]
###METHODS
#########

def dummyFunction(update=None):
	'''
	Does nothing, used as a placeholder
	'''
	pass

########
########CLASSES
########

class telegramHigh():

	LAST_UPDATE_ID = None

	"""telegramHigh"""
	def __init__(self, token):
		super(telegramHigh, self).__init__()
		self.bot = telegram.Bot(token)

	def breakLongMessage(self,msg):		
		'''
		Breaks a message that is too long.
		'''
		result_split = msg.split("\n")

		broken = []

		while result_split:
			result = ""
			while True:
				if result_split:
					result += result_split.pop(0)+"\n"
					print("result",result)
				else:
					break
				if len(result) > MAX_CHARS_PER_MESSAGE:
					break

			if result:
				n_parts = int( len(result)/MAX_CHARS_PER_MESSAGE +1 )

				for i in range(n_parts):
					broken += [result[i*len(result)//n_parts:(i+1)*len(result)//n_parts]]

		return broken

	def sendMessage(self,chat_id,message,key_markup="SAME",preview=True,markdown=False):
		logging.warning("Replying to " + str(chat_id) + ": " + message)
		fulltext = self.breakLongMessage(message)
		lS = LanguageSupport(chat_id)
		key_markup = lS.languageSupport(key_markup)
		for text in fulltext:
			#iterating over parts of a long split message
			while True:
				try:
					if text:
						self.bot.sendChatAction(chat_id,telegram.ChatAction.TYPING)
						self.bot.sendMessage(chat_id=chat_id,
							text=text,
							parse_mode='Markdown' if markdown else None,
							disable_web_page_preview=(not preview),
							reply_markup=(telegram.ReplyKeyboardMarkup(key_markup) if key_markup != "SAME" else None) if key_markup else telegram.ReplyKeyboardHide()
							)
				except Exception as e:
					if "Message is too long" in str(e):
						self.sendMessage(chat_id=chat_id
							,message="Error: Message is too long!"
							)
					elif ("urlopen error" in str(e)) or ("timed out" in str(e)):
						logging.error("Could not send message. Retrying! Error: " + str(e))
						sleep(3)
						continue
					else:
						logging.error("Could not send message. Error: " + str(e))
				break

	def sendPic(self,chat_id,pic,caption=None):
		while True:
			try:
				logging.debug("Picture: " + str(pic))
				self.bot.sendChatAction(chat_id,telegram.ChatAction.UPLOAD_PHOTO)
				#set file read cursor to the beginning. This ensures that if a file needs to be re-read (may happen due to exception), it is read from the beginning.
				pic.seek(0)
				self.bot.sendPhoto(chat_id=chat_id,photo=pic,caption=caption)
			except Exception as e:
				logging.error("Could not send picture. Retrying! Error: " + str(e))
				sleep(1)
				continue
			break

	def getUpdates(self):
		'''
		Gets updates. Retries if it fails.
		'''
		#if getting updates fails - retry
		updates = []
		while True:
			try:
				updates = self.bot.getUpdates(offset=self.LAST_UPDATE_ID)
			except Exception as e:
				logging.error("Could not read updates. Retrying! Error: " + str(sys.exc_info()[-1].tb_lineno) + ": " + str(e))
				sleep(1)
				continue
			break
		return updates

	def downloadPhoto(self,u,custom_filepath=None):
		"""
		Downloads a photo in a given update, if there is any.
		:param u: an update from getUpdates()
		:return: file extension
		"""
		file_ext=""
		if u.message.photo:
			# there are several photos in one message. The last one in the list is the highest resolution
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
				if(directory):
					makedirs(directory,exist_ok=True)
			#download the file to a given directory
			File.download(custom_path=custom_filepath)
		else:
			logging.warning("No photo in this message",str(u))
		return file_ext

	def echo(self,processingFunction=dummyFunction,periodicFunction=dummyFunction):
		bot= self.bot

		periodicFunction()

		updates = self.getUpdates()

		#main message processing routine
		for update in updates:
			logging.warning("Received message: " + str(update.message.chat_id) + " " + update.message.from_user.username + " " + update.message.text)

			processingFunction(update)

			# Updates global offset to get the new updates
			self.LAST_UPDATE_ID = update.update_id + 1