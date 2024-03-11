FROM python:3.8-slim

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git && \
    apt-get install -y vim

WORKDIR /tmp
COPY requirements.txt .

ENV PYTHONUNBUFFERED=True \
    PORT=${PORT:-9090}

RUN apt install --no-install-recommends -y libgl1 libglib2.0-0 libpython3-dev gnupg g++ libusb-1.0-0
RUN apt-get install ffmpeg libsm6 libxext6 -y
RUN pip install -r requirements.txt --no-cache-dir

WORKDIR /app

COPY *.py /app/

CMD exec gunicorn --preload --bind :$PORT --workers 1 --threads 8 --timeout 0 _wsgi:app
