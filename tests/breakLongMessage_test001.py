#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
from random import randint
from telegramHigh import telegramHigh

msg="".join([chr(randint(65,122)) for i in range(10**4)])

print(msg)
print(telegramHigh.breakLongMessage(msg))
