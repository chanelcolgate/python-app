import rabbitpy
import os

# Trong rabbitmq container go them dong lenh nay
# rabbitmq-plugins enable rabbitmq_consistent_hash_exchange

with rabbitpy.Connection(os.environ["RABBITMQ_URL"]) as connection:
    with connection.channel() as channel:
        # for exchange_name in ["rpc-replies", "direct-rpc-requests"]:
        #     exchange = rabbitpy.Exchange(
        #         channel, exchange_name, exchange_type="direct"
        #     )
        #     exchange.declare()
        dch = rabbitpy.Exchange(channel, "rpc-replies", exchange_type="direct")
        dch.declare()

        xch = rabbitpy.Exchange(
            channel,
            "rpc-requests",
            exchange_type="x-consistent-hash",
            arguments={"hash-header": "image-hash"},
        )
        xch.declare()
