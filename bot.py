import os
import logging
import hashlib
from datetime import datetime

from message_creator import MessageCreator
from configs import WEBHOOK_BASE_URL, BOT_SECRET, KEY, BOT_ADMIN_ID

from telegram import Update
from telegram.ext import Application, CommandHandler
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

message_creator = MessageCreator()
url_prefix_gitlab = WEBHOOK_BASE_URL + "/gitlab/"
url_prefix_github = WEBHOOK_BASE_URL + "/github/"

class BotContainer(object):
    pass
bot_container = BotContainer()

def get_token(id):
    hash_object = hashlib.md5((str(id) + KEY).encode())
    hex_dig = hash_object.hexdigest()
    return str(hex_dig)

async def new_gitlab(update, context, log_the_event=True):
    bot = update.get_bot()
    id = update.message.chat_id
    if id < 0:
        id = "n" + str(-id)
    else:
        id = "p" + str(id)
    if log_the_event:
        await log_text("new_gitlab " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    await bot.sendMessage(update.message.chat_id,
        text=message_creator.new_gitlab(url_prefix_gitlab + id, get_token(id)), parse_mode=ParseMode.HTML)

async def new_github(update, context, log_the_event=True):
    bot = update.get_bot()
    id = update.message.chat_id
    if id < 0:
        id = "n" + str(-id)
    else:
        id = "p" + str(id)
    if log_the_event:
        await log_text("new_github " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    await bot.sendMessage(update.message.chat_id,
        text=message_creator.new_github(url_prefix_github + id, get_token(id)), parse_mode=ParseMode.HTML)

async def start(update, context):
    bot = update.get_bot()
    await log_text("start " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    await new_gitlab(update, context, log_the_event=False)
    await new_github(update, context, log_the_event=False)

async def help_gitlab(update, context):
    bot = update.get_bot()
    await log_text("help_gitlab " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    await bot.sendMessage(update.message.chat_id, text=message_creator.help_gitlab(), parse_mode=ParseMode.MARKDOWN)

async def help_github(update, context):
    bot = update.get_bot()
    await log_text("help_github " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    await bot.sendMessage(update.message.chat_id, text=message_creator.help_github(), parse_mode=ParseMode.MARKDOWN)

async def log_text(line, bot=None):
    try:
        if bot:
            await bot.sendMessage(BOT_ADMIN_ID, text=(str(datetime.now()) + " " + str(line)))
    except:
        pass
    with open(os.path.join(os.path.dirname(__file__),"logs.txt"), "a") as f:
        f.write(str(datetime.now()) + " " + str(line) + "\n")


async def create_bot():
    bot_app = (
        Application.builder().token(BOT_SECRET).updater(None).build()
    )

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("new_gitlab", new_gitlab))
    bot_app.add_handler(CommandHandler("new_github", new_github))
    bot_app.add_handler(CommandHandler("help_gitlab", help_gitlab))
    bot_app.add_handler(CommandHandler("help_github", help_github))

    await bot_app.bot.set_webhook(url=f"{WEBHOOK_BASE_URL}/telegram", allowed_updates=Update.ALL_TYPES)

    return bot_app
