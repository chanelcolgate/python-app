import os
import rabbitpy
import time
import json
from datetime import datetime

import utils
import requests

# Open the connection and the channel
connection = rabbitpy.Connection()
channel = connection.channel()

# Create the worker queue
queue_name = f"rpc-worker-{os.getpid()}"
queue = rabbitpy.Queue(
    channel, queue_name, auto_delete=True, durable=False, exclusive=True
)

# Declare the worker queue
if queue.declare():
    print("Worker queue declared")

# Bind the worker queue
if queue.bind("direct-rpc-requests", "detect-objects"):
    print("Worker queue bound")

# Consume messages from RabbitMQ
for message in queue.consume_messages():
    # Display how long it took for the message to get here
    duration = time.time() - message.properties["timestamp"].timestamp()
    print(f"Received RPC request published {duration:.2f} seconds ago")

    # Write out the message body to a tempfile for facial detection process
    temp_file = utils.write_temp_file(message.body, message.properties["content_type"])

    # Detect objects
    url = "http://localhost:3000/annotation"
    payload = {}
    files = [("", (temp_file.split("/")[-1], open(temp_file, "rb"), "image/jpeg"))]
    headers = {"accept": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    body = json.loads(response.text)

    # Build response properties including the timestamp from the first publish
    properties = {
        "app_id": "Consumer",
        "content_type": message.properties["content_type"],
        "headers": {"first_publish": message.properties["timestamp"]},
    }

    # The result file cound just be the original image if nothing detected
    # body = utils.read_image(temp_file)

    # Remove the temp file
    # os.unlink(temp_file)

    # REmove the result file
    # os.unlink(result_file)

    # Publish the response
    response = rabbitpy.Message(channel, body, properties)
    response.publish("rpc-replies", message.properties["reply_to"])

    # Acknowledge the delivery of the RPC request message
    message.ack()
