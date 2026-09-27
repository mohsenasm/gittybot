# GittyBot
Git integration for Telegram Messenger ✌️

Using [@gittybot](https://t.me/Gittybot), you can easily receive Git events, such as push and CI/CD pipeline events, in your Telegram groups or chats.

## Usage

Simply go to [@gittybot](https://t.me/Gittybot) and type `/start`. It will send you instructions for adding GittyBot’s webhook address to your GitHub/GitLab repositories.

Feel free to contact me if you have any ideas for improvement.

If you use this bot, please give this repo a star ⭐️.

## Deployment

1. Create a Cloudflare Worker with the content of [worker.js](worker.js).
2. Create environment variables for:
   - `BOT_TOKEN`: the token given by BotFather
   - `BOT_SECRET`: a random string
   - `GIT_WEBHOOK_KEY`: another random string
   - `GIT_WEBHOOK_BASE_URL`: the webhook URL, starting with `https://` and with no trailing `/`
   - `BOT_ADMIN_ID`: a Telegram ID to send logs to

## Privacy

As you can see in the source code, the only data that is logged is Telegram chat info, which is stored for critical notifications, such as when you need to change the webhook URL.  
Your Git repository name and commit messages will not be saved or logged.  
Because the project uses a Cloudflare Worker, Cloudflare can see the content that passes through it.

## License

GNU General Public License

This project also uses code from [telegram-bot-cloudflare](https://github.com/cvzi/telegram-bot-cloudflare), licensed under CC0-1.0.
