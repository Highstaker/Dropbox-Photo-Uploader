#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import logging
import threading

import pickle


class ListThreadedSaver(object):
	"""Class that handles saving of a list to a file in a thread-safe manner."""
	def __init__(self, filename, load=True):
		super(ListThreadedSaver, self).__init__()
		# path and filename to a file in which the list is saved
		self.filename = filename

		# the main lock
		self.mutex = threading.Lock()

		#the list that will be modified and saved
		self.__main_list = []

		# try loading from file, if it exists
		if load:
			self.__load_file()

	def __load_file(self):
		"""
		Load the file
		:return: None
		"""
		try:
			with open(self.filename, 'rb') as f:
				self.__main_list = pickle.load(f)
				logging.warning(("self.__main_list", self.__main_list))
		except FileNotFoundError:
			logging.warning("List backup file %s not found. Starting with empty list!" % self.filename)
		except EOFError:
			logging.warning("Unexpected end of file while loading %s. Starting with empty list!" % self.filename)

	def __save_file(self):
		"""
		Saves list to file
		:return: None
		"""
		with open(self.filename, 'wb') as f:
			pickle.dump(self.__main_list, f, pickle.HIGHEST_PROTOCOL)

	def append_to_list(self, value, save=True):
		"""
		Appends a value to the list.
		:param value: a value to append to list
		:return: None
		"""
		with self.mutex:
			self.__main_list.append(value)
			if save:
				self.__save_file()

	def pop_first(self, save=True):
		"""
		Removes the first value in the list
		:return: the removed value
		"""
		with self.mutex:
			try:
				val = self.__main_list.pop(0)
				if save:
					self.__save_file()
			except IndexError:
				val = None
			return val

	def list_generator(self):
		"""
		A generator that returns all elements of __main_list
		:return:
		"""
		for i in self.__main_list:
			yield i
