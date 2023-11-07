FROM python:3.11

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["gunicorn", "-c", "gunicorn.config.py", "app:application"]
EXPOSE 5000