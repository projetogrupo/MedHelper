FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
COPY src/ ./src/
COPY manage.py .

RUN pip install --no-cache-dir -r requirements.txt

ENV DJANGO_SETTINGS_MODULE=medhelper.settings

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]