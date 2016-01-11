#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import dropbox

TOKEN = "PrgydhBbNnYAAAAAAAET8OUX2WaXr2dUWlzAherSTm6vGlhrIqLfJMGaY_k-APhK"

dbx = dropbox.Dropbox(TOKEN)

print("Account test: ", dbx.users_get_current_account())

dbx.files_upload("Hello, World!", "/test.txt"
				 , autorename=False
				 # , mode=dropbox.files.WriteMode("update",value="aaaaaaaab")
				 )

