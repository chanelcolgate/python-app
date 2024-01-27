import os
import time
from typing import List, Any, Union, Dict, Optional

import requests
import rabbitpy
from fastapi import APIRouter, HTTPException, status, Query, Body, Depends

import utils
from src.models.image_display import ImageDisplayPublic, ImageDisplayCreate
from src.settings import Settings

settings = Settings()

image_display_router = APIRouter(tags=["Image Display"])


@image_display_router.post("/object-detection")
async def create_object_detection(body: ImageDisplayCreate = Body(...)) -> dict:
    if settings.DEBUG:
        print(body.dict(exclude_unset=True))

    connection = rabbitpy.Connection()
    channel = connection.channel()

    exchange = rabbitpy.DirectExchange(channel, "rpc-replies")
    exchange.declare()

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

    image_url = body.dict(exclude_unset=True)["image"]
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

    # Display the result
    print(message.body, message.properties["content_type"])
    print("RPC requests processed")
    channel.close()
    connection.close()

    return {"message": "Image Display created successfully"}
