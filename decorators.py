#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import threading


def run_in_thread(func):
	def run(*args, **kwargs):
		t = threading.Thread(target=func, args=args, kwargs=kwargs)
		t.start()
		return t
	return run
