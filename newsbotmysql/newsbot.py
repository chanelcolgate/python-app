from time import sleep
from peewee import OperationalError
import pymysql

from states import States, log
from telegram import handle_incoming_messages
from models import *


def get_last_updated():
    try:
        with open("last_updated.txt", "r") as f:
            try:
                last_updated = int(f.read())
            except ValueError:
                last_updated = 0
        f.close()
    except FileNotFoundError:
        last_updated = 0
    log.debug(f"Last updated id: {last_updated}")
    return last_updated


if __name__ == "__main__":
    log.info("Starting up")
    log.info("Waiting for 60 seconds for db to come up")
    sleep(10)

    log.info("Checking on dbs")
    try:
        db.connect()
    except OperationalError as e:
        error_code, message = e.args[0], e.args[1]
        if error_code == 1049:
            db_connection = pymysql.connect(host="mysql", user="root", password="mysql")
            db_connection.cursor().execute("CREATE DATABASE newsbot")
            db_connection.close()
        db.create_tables([Source, Request, Message], True)

    try:
        States.last_updated = get_last_updated()
        while True:
            handle_incoming_messages(States.last_updated)
    except KeyboardInterrupt:
        log.info("Received KeybInterrupt, exiting")
