FROM python:3.8.5-alpine

ENV APP_HOME /app
WORKDIR $APP_HOME

COPY requirements.txt .

RUN \
  python3 -m pip install --upgrade pip && \
  python3 -m pip install -r requirements.txt --no-cache-dir

COPY . .

ENTRYPOINT [ "python" ]
CMD ["main.py"]
