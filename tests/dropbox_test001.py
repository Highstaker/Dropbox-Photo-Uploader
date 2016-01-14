#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import dropbox
from random import getrandbits
from os import path

TOKEN_FILENAME = "DB_token"
with open(path.join(path.dirname(path.realpath(__file__)), TOKEN_FILENAME),'r') as f:
	TOKEN = f.read().replace("\n", "")

dbx = dropbox.Dropbox(TOKEN)

print("Account test: ", dbx.users_get_current_account())

dbx.files_upload("Hello, World!", "/test.txt"
				 , autorename=True
				 )

random_folder_name = hex(getrandbits(128))[2:]

# dbx.files_create_folder("/" + random_folder_name + "/test_folder001")

dbx.files_upload(open("/tmp/001.jpg",'rb'), "/" + random_folder_name + "/test2.jpg"
				 , autorename=True
				 )