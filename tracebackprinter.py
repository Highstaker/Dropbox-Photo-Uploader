#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import sys, traceback

def full_traceback():
	"""
	Returns a full traceback to an exception
	:return:
	"""
	exc_type, exc_value, exc_traceback = sys.exc_info()
	a = traceback.format_exception(exc_type, exc_value, exc_traceback)
	a = "".join(a)
	return a