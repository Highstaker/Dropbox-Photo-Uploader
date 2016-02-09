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

# dbx.files_upload(open("/tmp/001.jpg",'rb'), "/" + random_folder_name + "/test2.jpg"
# 				 , autorename=True
# 				 )

print("Root metadata:", dbx.files_get_metadata("/001"))
print("File metadata:", dbx.files_get_metadata("/001/2test.txt"))
try:
	dbx.files_delete("/001/test.txt")
except dropbox.exceptions.ApiError as e:
	print("Error:", "not_found" in str(e))

print("Folder contents:", dbx.files_list_folder("/001"))


space_usage = dbx.users_get_space_usage()
print("Space usage: ", space_usage)

used_space = space_usage.used
total_allocated_space = space_usage.allocation.get_individual().allocated

print("Used space: %.2f GB" % (used_space/1024**3))
print("Total space: %.2f GB" % (total_allocated_space/1024**3))
print("Free space: %.2f GB" % ((total_allocated_space - used_space)/1024**3))

