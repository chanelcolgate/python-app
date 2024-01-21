from peewee import (
    Model,
    PrimaryKeyField,
    IntegerField,
    CharField,
    DateTimeField,
    MySQLDatabase,
)

db = MySQLDatabase(
    host="mysql", port=3306, user="root", password="mysql", database="newsbot"
)


class BaseModel(Model):
    class Meta:
        database = db


class Source(BaseModel):
    # person_id = PrimaryKeyField()
    person_id = CharField(primary_key=True, max_length=10)
    fetch_from = CharField()


class Request(BaseModel):
    id = PrimaryKeyField()
    from_id = IntegerField(index=True)
    request_text = CharField()
    received_time = DateTimeField()


class Message(BaseModel):
    id = PrimaryKeyField()
    sent_to_id = IntegerField(index=True)
    sent_message = CharField()
    sent_time = DateTimeField()
