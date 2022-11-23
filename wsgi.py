import os
import bot
from flask import Flask, request, send_from_directory
from telegram import Update
from configs import BOT_SECRET, PORT, WEBHOOK_BASE_URL, LOG_VIEWER_USERNAME, LOG_VIEWER_PASSWORD
from git_webhook import git_app

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

import logging
import os
application = Flask(__name__)


auth = HTTPBasicAuth()
users = dict()
users[LOG_VIEWER_USERNAME] = generate_password_hash(LOG_VIEWER_PASSWORD)
@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
print("bot.setup {}".format(WEBHOOK_BASE_URL))
update_queue, bot_instance = bot.setup(webhook_url='{}/{}'.format(
    WEBHOOK_BASE_URL,
    BOT_SECRET
))
print("register git_app blueprint")
application.register_blueprint(git_app)


@application.route('/')
def not_found():
    """Server won't respond in Heroku if we don't handle the root path."""
    return 'Hello!!'


@application.route('/' + BOT_SECRET, methods=['GET', 'POST'])
def webhook():
    if request.json:
        update_queue.put(Update.de_json(request.get_json(force=True), bot_instance))
    return ''


@application.route('/logs/')
@auth.login_required
def logs():
    return send_from_directory(os.path.dirname(__file__), 'logs.txt')


@application.route('/ping/')
def ping():
    return "pong"


if __name__ == '__main__':
    host = "0.0.0.0"
    print("run application on {}:{}".format(host, PORT))
    application.run(host=host, port=PORT)
