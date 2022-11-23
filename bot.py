import os
from queue import Queue
from threading import Thread
from telegram import Bot, ParseMode
from telegram.ext import Dispatcher, MessageHandler, Updater, CommandHandler
from message_creator import MessageCreator
from configs import *
import hashlib
from datetime import datetime

import logging
logger = logging.getLogger(__name__)
message_creator = MessageCreator()
url_prefix_gitlab = WEBHOOK_BASE_URL + "/gitlab/"
url_prefix_github = WEBHOOK_BASE_URL + "/github/"


class BotContainer(object):
    pass
bot_container = BotContainer()
# bot_container.myBot


def get_token(id):
    hash_object = hashlib.md5((str(id) + KEY).encode())
    hex_dig = hash_object.hexdigest()
    return str(hex_dig)


def new_gitlab(update, context):
    bot = context.bot
    id = update.message.chat_id
    if id < 0:
        id = "n" + str(-id)
    else:
        id = "p" + str(id)
    log_text("new_gitlab " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    bot.sendMessage(update.message.chat_id,
                    text='Set this url in your gitlab webhook setting:\nURL: {}\nSecret Token: {}'
                    .format(url_prefix_gitlab + id, get_token(id)))


def new_github(update, context):
    bot = context.bot
    id = update.message.chat_id
    if id < 0:
        id = "n" + str(-id)
    else:
        id = "p" + str(id)
    log_text("new_github " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    bot.sendMessage(update.message.chat_id,
                    text='Set this url in your github webhook setting:\nURL: {}\nSecret Token: {}'
                    .format(url_prefix_github + id, get_token(id)))


def new_gitlab_github(update, context):
    bot = context.bot
    id = update.message.chat_id
    if id < 0:
        id = "n" + str(-id)
    else:
        id = "p" + str(id)
    log_text("start " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    bot.sendMessage(update.message.chat_id,
                    text='Set this url in your gitlab webhook setting:\nURL: {}\nSecret Token: {}'
                    .format(url_prefix_gitlab + id, get_token(id)))
    bot.sendMessage(update.message.chat_id,
                    text='Set this url in your github webhook setting:\nURL: {}\nSecret Token: {}'
                    .format(url_prefix_github + id, get_token(id)))


def help_gitlab(update, context):
    bot = context.bot
    log_text("help_gitlab " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    bot.sendMessage(update.message.chat_id, text=message_creator.help_gitlab(), parse_mode=ParseMode.MARKDOWN)
    new_gitlab(bot, update)


def help_github(update, context):
    bot = context.bot
    log_text("help_github " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    bot.sendMessage(update.message.chat_id, text=message_creator.help_github(), parse_mode=ParseMode.MARKDOWN)
    new_github(bot, update)


def echo(update, context):
    bot = context.bot
    bot.sendMessage(update.message.chat_id, text=update.message.text)


def error(update, context):
    logger.warn('Update "%s" caused error "%s"' % (update, context.error))
    log_text('error update: "%s" caused error: "%s"' % (update, context.error))


def log_text(line, bot=None):
    try:
        if bot:
                bot.sendMessage(85984800, text=(str(datetime.now()) + " " + str(line)))
    except:
        pass
    with open(os.path.join(os.path.dirname(__file__),"all_logs.txt"), "a") as f:
        f.write(str(datetime.now()) + " " + str(line) + "\n")


def setup(webhook_url=None):
    """If webhook_url is not passed, run with long-polling."""
    logging.basicConfig(level=logging.WARNING)
    if webhook_url:
        bot = Bot(BOT_SECRET)
        update_queue = Queue()
        dp = Dispatcher(bot, update_queue)
    else:
        updater = Updater(BOT_SECRET)
        bot = updater.bot
        dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", new_gitlab_github))
    dp.add_handler(CommandHandler("new_gitlab", new_gitlab))
    dp.add_handler(CommandHandler("new_github", new_github))
    dp.add_handler(CommandHandler("help_gitlab", help_gitlab))
    dp.add_handler(CommandHandler("help_github", help_github))

    if TEST_MODE:
        dp.add_handler(MessageHandler([], echo))

    # log all errors
    dp.add_error_handler(error)
    bot_container.bot = bot
    if webhook_url:
        bot.set_webhook(url=webhook_url)
        thread = Thread(target=dp.start, name='dispatcher')
        thread.start()
        return update_queue, bot
    else:
        bot.set_webhook()  # Delete webhook
        updater.start_polling()
        updater.idle()




if __name__ == '__main__':
    setup()
