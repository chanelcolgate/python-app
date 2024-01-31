import rabbitpy

from src.settings import settings

connection = rabbitpy.Connection(settings.RABBITMQ_URL)
channel = connection.channel()

exchange = rabbitpy.DirectExchange(channel, "rpc-replies")
exchange.declare()
