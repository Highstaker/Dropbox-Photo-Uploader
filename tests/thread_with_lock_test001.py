#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
import threading
from time import sleep

class A(object):
	"""docstring for A"""
	def __init__(self):
		super(A, self).__init__()
		self.mutex = threading.Lock()

	def func(self,a,Sleep=False):
		print(a + " called func()")
		with self.mutex:
			print(a + " entered mutex")
			if Sleep:
				print("="*20)
				sleep(3)
			print(a + " finished")
		
class B(object):
	"""docstring for B"""
	def __init__(self):
		super(B, self).__init__()
		self.insA = A()
		t = threading.Thread(target=self.test_thread)
		t.start()
		t = threading.Thread(target=self.test_thread)
		t.start()
		self.insA.func("main",Sleep=True)
		t = threading.Thread(target=self.test_thread)
		t.start()

	def test_thread(self):
		self.insA.func("thread",Sleep=True)

def main():
	b = B()

if __name__ == '__main__':
	main()