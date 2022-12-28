# -*- coding: utf-8 -*-
from flask import Flask, request, Response, Blueprint
from message_creator import MessageCreator
import hashlib
import telegram
import hmac
from configs import WEBHOOK_BASE_URL
from bot import log_text, bot_container, get_token

git_app = Blueprint('git_app', __name__)
message_creator = MessageCreator()
url_prefix_gitlab = WEBHOOK_BASE_URL + "/gitlab/"
url_prefix_github = WEBHOOK_BASE_URL + "/github/"

# Enable logging
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


@git_app.route('/gitlab/<string:id>', methods=["POST"])
def gitlab(id):
    can_send, message = message_creator.gitlab(request)

    if request.headers['X-Gitlab-Token'] != get_token(id):
        return Response(status=403)

    if can_send:
        chat_id = id[1:]
        if id[0] == 'n':
            chat_id = -1 * int(chat_id)
        log_text("gitlab " + str(chat_id))
        bot_container.bot.sendMessage(chat_id, text=message, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
    return Response(status=200)


@git_app.route('/github/<string:id>', methods=["POST"])
def github(id):
    can_send, message = message_creator.github(request)

    signature = request.headers.get('X-Hub-Signature')
    data = request.data
    if not validate_github_signature(get_token(id), data, signature):
        return Response(status=403)

    if can_send:
        chat_id = id[1:]
        if id[0] == 'n':
            chat_id = -1 * int(chat_id)
        log_text("github " + str(chat_id))
        bot_container.bot.sendMessage(chat_id, text=message, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
    return Response(status=200)


def validate_github_signature(token, data, signature):
    GitHub_secret = bytes(token, 'UTF-8')
    mac = hmac.new(GitHub_secret, msg=data, digestmod=hashlib.sha1)
    return hmac.compare_digest('sha1=' + mac.hexdigest(), signature)
