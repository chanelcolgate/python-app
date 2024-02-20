import rabbitpy
import os

with rabbitpy.Connection(os.environ["RABBITMQ_URL"]) as connection:
    with connection.channel() as channel:
        for exchange_name in ["rpc-replies", "direct-rpc-requests"]:
            exchange = rabbitpy.Exchange(
                channel, exchange_name, exchange_type="direct"
            )
            exchange.declare()
