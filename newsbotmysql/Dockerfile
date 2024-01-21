FROM python:3.8-alpine

RUN apk add gcc musl-dev python3-dev libffi-dev openssl-dev
WORKDIR /apps
COPY . .
# RUN ["pip", "install", "-r", "requirements.txt"]
RUN pip install -r requirements.txt
CMD ["python", "newsbot.py"]
