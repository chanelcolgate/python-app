import os
import rabbitpy
import time
import utils

# Open the channel and connection
connection = rabbitpy.Connection()
channel = connection.channel()

exchange = rabbitpy.DirectExchange(channel, "rpc-replies")
exchange.declare()

# Create the response queue that will automatically delete, is not
# durable and is exclusive to this publisher
queue_name = f"response-queue-{os.getpid()}"
response_queue = rabbitpy.Queue(
    channel, queue_name, auto_delete=True, durable=False, exclusive=True
)

# Declare the response queue
if response_queue.declare():
    print("Response queue declared")

# Bind the response queue
if response_queue.bind("rpc-replies", queue_name):
    print("Response queue bound")

# image_url = "https://datasets-server.huggingface.co/assets/keremberke/valorant-object-detection/--/full/train/13/image/image.jpg"
image_url = "https://datasets-server.huggingface.co/assets/keremberke/valorant-object-detection/--/full/train/2/image/image.jpg"
# image_url = "https://transform.roboflow.com/J6YLfA0RLPhDyMbKbQPiq2jlqsF3/cd98e4c0ff1c3359947bae87f2174b11/thumb.jpg"
if not image_url[:8].startswith(("https://", "http://")):
    image_url = "http://" + image_url

# start job
print(f"Sending request for image: {image_url}")
temp_file = utils.read_and_write_url(image_url)
message = rabbitpy.Message(
    channel,
    utils.read_image(temp_file),
    {"content_type": utils.mime_types(temp_file), "reply_to": queue_name},
    opinionated=True,
)

# Publish
message.publish("direct-rpc-requests", "detect-objects")

# Loop util there is a response message
message = None
while not message:
    time.sleep(0.5)
    message = response_queue.get()

# Remove the temp file
os.unlink(temp_file)

# Ack the response message
message.ack()

# Calculate how long it took from publish to response
duration = time.time() - time.mktime(message.properties["headers"]["first_publish"])
print(f"Facial detection RPC call for image total duration: {duration}")

print("RPC requests processed")

channel.close()
connection.close()
