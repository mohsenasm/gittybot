# GittyBot
Git Integration for Telegram messenger ✌️

By using [@gittybot](https://t.me/Gittybot) you can easily receive git events, such as push and CI/CD pipeline events, in your telegram groups or chats.

## Usage

Simply go to [@gittybot](https://t.me/Gittybot) and type /start. It will send you the instruction to add the GittyBot's webhook address to your GitHub/GitLab repositories.

Feel free to contact me, if you have any ideas for improvement.

If you are using this bot, please give this repo a star ⭐️.

## Deployment

1. Create a file named `secret.env` with the following env:

```env
BOT_ADMIN_ID="your_telegram_chat_id"
WEBHOOK_BASE_URL="https://..."
KEY="a_random_key"
TEST_MODE="false"
TEST_BOT_SECRET="..."
BOT_SECRET="..."
LOG_VIEWER_USERNAME="..."
LOG_VIEWER_PASSWORD="..."
```

2. Create `docker-compose.yml` like the provided `docker-compose.example.yml`.

3. `docker-compose up --build -d`.

## Privacy

As you can check the source code, the only data that is logged is chats' telegram info, which is stored for critical notifications such as situations when you need to change the webhook URL.
Your git repository name or commit messages will not be saved and/or logged.

# Lisence
GNU General Public License
