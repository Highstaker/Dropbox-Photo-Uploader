#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import pickle
from os import path
import logging


# noinspection PyPep8
class SubscribersHandler(object):
	"""docstring for SubscribersHandler"""

	subscribers = dict()

	def __init__(self, savefile_path, savefile_name, initial_params, from_file=True):
		super(SubscribersHandler, self).__init__()
		self.subscribers_backup_filename = path.join(savefile_path, savefile_name)  # backup filename
		self.initial_params = initial_params  # a list of parameters to initialize a user with

		if from_file:
			self.loadSubscribers()  # load subscribers from a file, if it exists

	def loadSubscribers(self):
		"""
		Loads subscribers from a file. Show warning if it doesn't exist.
		"""
		try:
			with open(self.subscribers_backup_filename, 'rb') as f:
				self.subscribers = pickle.load(f)
				logging.warning(("self.subscribers", self.subscribers))
		except FileNotFoundError:
			logging.warning("Subscribers backup file not found. Starting with empty list!")

	def saveSubscribers(self):
		"""
		Saves a subscribers list to file
		"""
		with open(self.subscribers_backup_filename, 'wb') as f:
			pickle.dump(self.subscribers, f, pickle.HIGHEST_PROTOCOL)

	def init_user(self, chat_id, force=False, params=None, save=True):
		"""
		Initializes a user with initialparams
		:param chat_id: user's chat id number
		:param force: if False, do not initialize a user if they already exist
		:param params: a dictionary of parameters that should be assigned on initialization
		:param save: saves the subscribers list to file if True and if initialization took place
		:return: None
		"""
		if not (chat_id in self.subscribers.keys()) or force:
			# T T = T
			# F T = T
			# T F = T
			# F F = F
			self.subscribers[chat_id] = self.initial_params.copy()
			if params:
				for i in params:
					self.subscribers[chat_id][i] = params[i]
			if save:
				self.saveSubscribers()

	def get_param(self, chat_id, param):
		"""
		Returns a parameter from subscribers list.
		:param chat_id: user's chat id number
		:param param: a key of a parameter to be retrieved
		:return: a specified parameter
		"""
		return self.subscribers[chat_id][param]

	def set_param(self, chat_id, param, value, save=True):
		"""
		Sets the given parameter to a certain value
		:param chat_id: user's chat id number
		:param param: a key of a parameter to be modifieded
		:param value: value to set to a parameter
		:param save: saves the subscribers list to file if True
		:return: None
		"""
		self.subscribers[chat_id][param] = value
		if save:
			self.saveSubscribers()
