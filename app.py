import os
import sys
import random
import asyncio
import logging
from http import HTTPStatus

from telegram import Update

from flask import Flask, Response, make_response, request, send_from_directory, redirect
from asgiref.wsgi import WsgiToAsgi

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from gunicorn.arbiter import Arbiter
from uvicorn.main import Server
from uvicorn.workers import UvicornWorker

from bot import create_bot
from configs import LOG_VIEWER_USERNAME, LOG_VIEWER_PASSWORD
from git_webhook import git_app

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class TelegramBotUvicornWorker(UvicornWorker):
    async def _serve(self) -> None:
        self.config.app = self.wsgi
        server = Server(config=self.config)
        self._install_sigquit_handler()

        # sleep to prevent Telegram's Flood control
        await asyncio.sleep(random.randint(0, 5))
        
        bot_app = await self.config.app.get_bot_app()
        async with bot_app:
            await bot_app.start()
            await server.serve(sockets=self.sockets)
            await bot_app.stop()

        if not server.started:
            sys.exit(Arbiter.WORKER_BOOT_ERROR)


class LazyApp:
    def __init__(self):
        self._app = None
    
    async def get_bot_app(self):
        if self._app is None:
            self._app = await create_app()
        return self._app.bot_app

    async def __call__(self, scope, receive, send):
        if self._app is None:
            self._app = await create_app()
        await self._app(scope, receive, send)



async def create_app() -> None:
    bot_app = await create_bot()

    auth = HTTPBasicAuth()
    users = dict()
    users[LOG_VIEWER_USERNAME] = generate_password_hash(LOG_VIEWER_PASSWORD)
    @auth.verify_password
    def verify_password(username, password):
        if username in users and \
                check_password_hash(users.get(username), password):
            return username

    flask_app = Flask(__name__)
    flask_app.register_blueprint(git_app)

    @flask_app.route('/')
    def root():
        return redirect("https://github.com/mohsenasm/gittybot/blob/main/README.md")
    
    @flask_app.post("/telegram")  # type: ignore[misc]
    async def telegram() -> Response:
        await bot_app.update_queue.put(Update.de_json(data=request.json, bot=bot_app.bot))
        return Response(status=HTTPStatus.OK)

    @flask_app.get("/ping")  # type: ignore[misc]
    async def ping() -> Response:
        response = make_response("pong", HTTPStatus.OK)
        response.mimetype = "text/plain"
        return response

    @flask_app.get('/logs/')
    @auth.login_required
    def logs():
        return send_from_directory(os.path.dirname(__file__), 'logs.txt')
    
    asgi_app = WsgiToAsgi(flask_app)
    asgi_app.bot_app = bot_app

    return asgi_app

app = LazyApp()
