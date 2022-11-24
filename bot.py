import os
from queue import Queue
from threading import Thread
from telegram import Bot, ParseMode
from telegram.ext import Dispatcher, MessageHandler, Updater, CommandHandler, filters
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


def new_gitlab(update, context, log_the_event=True):
    bot = context.bot
    id = update.message.chat_id
    if id < 0:
        id = "n" + str(-id)
    else:
        id = "p" + str(id)
    if log_the_event:
        log_text("new_gitlab " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    bot.sendMessage(update.message.chat_id,
        text=message_creator.new_gitlab(url_prefix_gitlab + id, get_token(id)), parse_mode=ParseMode.HTML)

def new_github(update, context, log_the_event=True):
    bot = context.bot
    id = update.message.chat_id
    if id < 0:
        id = "n" + str(-id)
    else:
        id = "p" + str(id)
    if log_the_event:
        log_text("new_github " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    bot.sendMessage(update.message.chat_id,
        text=message_creator.new_github(url_prefix_github + id, get_token(id)), parse_mode=ParseMode.HTML)


def start(update, context):
    bot = context.bot
    log_text("start " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    new_gitlab(update, context, log_the_event=False)
    new_github(update, context, log_the_event=False)


def help_gitlab(update, context):
    bot = context.bot
    log_text("help_gitlab " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    bot.sendMessage(update.message.chat_id, text=message_creator.help_gitlab(), parse_mode=ParseMode.MARKDOWN)


def help_github(update, context):
    bot = context.bot
    log_text("help_github " + str(update.message.chat_id) + " " + str(update.message.from_user.username) + " " + str(update.message.chat.title), bot)
    bot.sendMessage(update.message.chat_id, text=message_creator.help_github(), parse_mode=ParseMode.MARKDOWN)


def echo(update, context):
    bot = context.bot
    bot.sendMessage(update.message.chat_id, text=update.message.text)


def check_admin_command(update, context):
    bot = context.bot
    if (str(update.message.chat_id) == BOT_ADMIN_ID):
        lines = update.message.text.split("\n")
        if "!migrate_from_heroku_notification" == lines[0]:
            chat_ids = set()
            for l in lines[1:]:
                if len(l) > 0:
                    chat_ids.add(int(l))
            log_text("migrate_from_heroku_notification " + str(chat_ids), bot)
            for chat_id in chat_ids:
                if chat_id < 0:
                    id = "n" + str(-chat_id)
                else:
                    id = "p" + str(chat_id)
                try:
                    bot.sendMessage(
                        chat_id, 
                        text=message_creator.migrate_from_heroku_notification(
                            url_prefix_github + id, 
                            url_prefix_gitlab + id, 
                            get_token(id)), 
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True)
                except Exception as e:
                    log_text("error for " + str(chat_id) + " " + str(e), bot)
                else:
                    log_text("sent to " + str(chat_id), bot)



def error(update, context):
    logger.warn('Update "%s" caused error "%s"' % (update, context.error))
    log_text('error update: "%s" caused error: "%s"' % (update, context.error))


def log_text(line, bot=None):
    try:
        if bot:
            bot.sendMessage(BOT_ADMIN_ID, text=(str(datetime.now()) + " " + str(line)))
    except:
        pass
    with open(os.path.join(os.path.dirname(__file__),"logs.txt"), "a") as f:
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
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("new_gitlab", new_gitlab))
    dp.add_handler(CommandHandler("new_github", new_github))
    dp.add_handler(CommandHandler("help_gitlab", help_gitlab))
    dp.add_handler(CommandHandler("help_github", help_github))

    dp.add_handler(MessageHandler(filters.Filters.text | filters.Filters.command, check_admin_command))

    # if TEST_MODE:
    #     dp.add_handler(MessageHandler(filters.Filters.text | filters.Filters.command, echo))

    log_text("start the bot")

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
