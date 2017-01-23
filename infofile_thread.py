#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
from threading import Thread
from string import ascii_letters, punctuation, digits

import dropbox

from languagesupport import LanguageSupport

INFO_FILE_FILENAME = "info.txt"

INFO_FILE_DELETED_MESSAGE = {"EN": "Info file is deleted", "RU": "Информационный файл удалён"}
INFO_FILE_CREATED_MESSAGE = {"EN": "Info file is created", "RU": "Информационный файл создан"}
INFO_FILE_UPDATED_MESSAGE = {"EN": "Info file is updated", "RU": "Информационный файл обновлён"}


class InfofileThread(object):
	"""docstring for InfofileThread"""
	def __init__(self, bot, dbx, chat_id, folder_name, username, comment, user_language, recreate=False):
		super(InfofileThread, self).__init__()
		t = Thread(target=self._infofile_thread, args=(bot, dbx, chat_id, folder_name,
													username, comment, user_language, recreate,))
		t.start()
		
	def _infofile_thread(self, bot, dbx, chat_id, folder_name, username, comment, user_language, recreate):
		lS = LanguageSupport(user_language).languageSupport
		try:
			dbx.files_delete("/" + folder_name + "/" + INFO_FILE_FILENAME)
			if recreate:
				# TODO: this is bodging. Find a way to allow more symbols!
				#allow only alphanumeric
				allowed_symbols = ascii_letters + punctuation + digits
				username = "".join(i if i in allowed_symbols else "_" for i in username)
				comment = "".join(i if i in allowed_symbols else "_" for i in comment)
				dbx.files_upload("Photos by " + username + "\n\n" + comment, "/" + folder_name + "/" + INFO_FILE_FILENAME)
				bot.sendMessage(chat_id=chat_id
							, message=lS(INFO_FILE_UPDATED_MESSAGE)
							, key_markup="SAME"
							)
			else:
				bot.sendMessage(chat_id=chat_id
							, message=lS(INFO_FILE_DELETED_MESSAGE)
							, key_markup="SAME"
							)
		except dropbox.exceptions.ApiError as e:
			if "not_found" in str(e):
				if not recreate:
					dbx.files_upload("Photos by " + username + "\n\n" + comment, "/" + folder_name + "/" + INFO_FILE_FILENAME)
					bot.sendMessage(chat_id=chat_id
								, message=lS(INFO_FILE_CREATED_MESSAGE)
								, key_markup="SAME"
								)
