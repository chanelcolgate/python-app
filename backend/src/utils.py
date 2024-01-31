import os
import time
import json
import hashlib
import imghdr
import platform
from io import BytesIO

import rabbitpy
import requests
from PIL import Image

import utils
from src.settings import settings
from src.models.check import CheckPublic
from src.models.image_display import Checks


async def detect_objects(body) -> dict:
    connection = rabbitpy.Connection(settings.RABBITMQ_URL)
    channel = connection.channel()

    exchange = rabbitpy.DirectExchange(channel, "rpc-replies")
    exchange.declare()

    queue_name = f"response-queue-{os.getpid()}"
    response_queue = rabbitpy.Queue(
        channel,
        queue_name,
        auto_delete=True,
        durable=False,
    )

    if settings.DEBUG:
        # Declare the response queue
        if response_queue.declare():
            print("Response queue declared")

        # Bind the response queue
        if response_queue.bind("rpc-replies", queue_name):
            print("Response queue bound")

    response_queue.declare()
    response_queue.bind("rpc-replies", queue_name)

    program_id = body["program_id"]
    image_url = body["image"]
    if not image_url[:8].startswith(("https://", "http://")):
        image_url = "http://" + image_url

    if settings.DEBUG:
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

    if settings.DEBUG:
        # Calculate how long it took from publish to response
        duration = time.time() - time.mktime(
            message.properties["headers"]["first_publish"]
        )
        print(f"Facial detection RPC call for image total duration: {duration}")

        # Display the result
        print(json.loads(message.body), message.properties["content_type"])
        print("RPC requets processed")

    channel.close()
    connection.close()

    detection_dict, image_url = json.loads(message.body)
    checks = await Checks.filter(id=program_id)
    matrix_check_list = [
        CheckPublic.from_orm(check).dict(exclude={"name", "type_check"})
        for check in checks
    ]

    result_dict = dict()

    if settings.DEBUG:
        for matrix_check in matrix_check_list:
            sum_check = 0
            sum_matrix = 0
            error_string = ""
            for key, item in matrix_check.items():
                sum_matrix += matrix_check[key]
                try:
                    if matrix_check[key] <= detection_dict[key]:
                        result_dict[key] = detection_dict[key]
                        sum_check += detection_dict[key]
                    else:
                        error_string += f"Khong du {key}, "
                except KeyError:
                    error_string += f"Khong co {key}, "
            if sum_check >= sum_matrix:
                print(f"OK, {matrix_check}")
                break
            else:
                print(f"Fail, {error_string}")
        return {
            "message": "Image Display created successfully",
            "image_url": image_url.split("/")[-1],
        }

    message = ""
    reason = ""
    program_id = None
    for matrix_check in matrix_check_list:
        sum_check = 0
        sum_matrix = 0
        error_string = ""
        for key, item in matrix_check.items():
            if key != "id":
                sum_matrix += matrix_check[key]
                try:
                    if matrix_check[key] <= detection_dict[key]:
                        result_dict[key] = detection_dict[key]
                        sum_check += detection_dict[key]
                    else:
                        error_string += f"không đủ {key}, "
                except KeyError:
                    error_string += f"không có {key}, "
        # error_string = error_string.rstrip(", ")
        if sum_check >= sum_matrix:
            message = "Đạt"
            program_id = matrix_check["id"]
            reason = ""
            break
        else:
            message = "Không đạt"
            reason += error_string
    return {
        "result": message,
        "reason": reason.rstrip(", "),
        "program_id": program_id,
        "image_url": image_url.split("/")[-1],
    }


def read_and_write_url(image_url):
    h = hashlib.sha1()
    h.update(image_url.encode("utf-8"))
    filename = f"{h.hexdigest()}.jpg"
    try:
        # Make a GET requests to the image URL
        response = requests.get(image_url)
        response.raise_for_status()  # Check if the request was successuflly

        # Open the image using PIL
        image = Image.open(BytesIO(response.content))
        image = image.convert("RGB")

        # Save the image locally
        if not os.path.exists("src/tmp"):
            os.makedirs("src/tmp")
        filename = f"src/tmp/{filename}"
        image.save(filename)
        return filename
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error reading image from URL: {e}")
    except Exception as e:
        raise ValueError(f"Error writing image to {filename}: {e}")