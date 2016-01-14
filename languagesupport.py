#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

class LanguageSupport(object):
	"""docstring for LanguageSupport"""
	def __init__(self, lang):
		super(LanguageSupport, self).__init__()
		self.lang = lang

	def languageSupport(self, message):
		"""
		Returns a message depending on a language chosen by user
		:param message:
		"""
		lang = self.lang
		if isinstance(message, str):
			result = message
		elif isinstance(message, dict):
			try:
				result = message[lang]
			except:
				print("could not find langauge")#debug
				result = message["EN"]
		elif isinstance(message,list):
			# could be a key markup
			result = list(message)
			for n,i in enumerate(message):
				result[n] = self.languageSupport(i)
		else:
			result = ""

		print("languageSupport result:", result)#debug
		return result
