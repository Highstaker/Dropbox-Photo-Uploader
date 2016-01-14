#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

class LanguageSupport(object):
	"""docstring for LanguageSupport"""
	def __init__(self, chat_id):
		super(LanguageSupport, self).__init__()
		self.chat_id = chat_id

	def languageSupport(self,message):
		'''
		Returns a message depending on a language chosen by user
		'''
		chat_id = self.chat_id
		if isinstance(message,str):
			result = message
		elif isinstance(message,dict):
			try:
				result = message[self.subscribers[chat_id][0]]
			except:
				result = message["EN"]
		elif isinstance(message,list):
			#could be a key markup
			result = list(message)
			for n,i in enumerate(message):
				result[n] = self.languageSupport(i)
		else:
			result = " "
			
		return result
