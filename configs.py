import os
from dotenv import load_dotenv

if os.path.isfile("secret.env"):
    print("loading envs from secret.env")
    load_dotenv("secret.env")  # take environment variables from .env.

BOT_ADMIN_ID = os.environ['BOT_ADMIN_ID']
LOG_VIEWER_USERNAME = os.environ['LOG_VIEWER_USERNAME']
LOG_VIEWER_PASSWORD = os.environ['LOG_VIEWER_PASSWORD']
KEY = os.environ['KEY']
HEROKU_KEY = os.environ['HEROKU_KEY'] # for backward compatibility. will remove soon.
PORT = os.environ['PORT']
WEBHOOK_BASE_URL = os.environ['WEBHOOK_BASE_URL']

TEST_MODE = os.environ['TEST_MODE'] == "true"
if TEST_MODE:
    BOT_SECRET = os.environ['TEST_BOT_SECRET']
else:
    BOT_SECRET = os.environ['BOT_SECRET']

