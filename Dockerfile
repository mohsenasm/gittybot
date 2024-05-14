FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["gunicorn", "main:app", "-w", "2", "-k", "main.TelegramBotUvicornWorker"]