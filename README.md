# Dropbox-Photo-Uploader
A Telegram bot that uploads photos sent to it to Dropbox to a separate folder for each user.

##Deployment
Put your bot token to a file named "bot_token"
Get your Dropbox app token and put in to a file named "DB_token".
Put the shared link to your app folder to a file named "DB_shared_folder"
All these files should be in the script's folder.

##Dependencies

This program uses **Python 3**

This program relies on [python-telegram-bot](https://github.com/leandrotoledo/python-telegram-bot).
To install it, use: `pip3 install python-telegram-bot`

Dropbox access is handled by [this library](https://github.com/dropbox/dropbox-sdk-python)
To install it, use: `pip3 install dropbox`