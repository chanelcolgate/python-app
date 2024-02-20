FROM python:3.8-slim

ENV APP_HOME /app

WORKDIR $APP_HOME

COPY requirements.txt .

RUN apt-get update
RUN apt install --no-install-recommends -y python3-pip git zip curl htop libgl1 libglib2.0-0 libpython3-dev gnupg g++ libusb-1.0-0
RUN \
  python3 -m pip install --upgrade pip && \
  python3 -m pip install -r requirements.txt --no-cache-dir

COPY . .

ENTRYPOINT [ "python" ]
CMD ["main.py"]
