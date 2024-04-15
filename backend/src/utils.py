import os
import time
import json
import hashlib
import base64
import asyncio
import uuid
from io import BytesIO
from functools import wraps

import rabbitpy
import requests
import imagehash
from PIL import Image
from fastapi import HTTPException, Depends, status
from fastapi.security import APIKeyHeader

import utils
from src.settings import settings
from src.models.check import CheckPublic
from src.models.image_display import Checks, ImageUpdate, State, Images


def images_to_compare(imfile1, imfile2, hashfunc=imagehash.phash):
    img1, img2 = Image.open(imfile1), Image.open(imfile2)
    hash1 = hashfunc(img1)
    hash2 = hashfunc(img2)
    return hash1 - hash2


def timed_execution(func):
    @wraps(func)
    def timed_execute(*args, **kwargs):
        start_time = time.process_time()
        result = func(*args, **kwargs)
        end_time = time.process_time()
        run_time = end_time - start_time
        print(f"'{func.__name__}' took {run_time * 1000:.2f} ms")
        return result

    return timed_execute


def timed_execution_async(func):
    async def wrapper(*args, **kwargs):
        t = 0
        coro = func(*args, **kwargs)
        try:
            while True:
                t0 = time.perf_counter()
                future = coro.send(None)
                t1 = time.perf_counter()
                t += t1 - t0
                while not future.done():
                    await asyncio.sleep(0)
                future.result()
        except StopIteration as e:
            print(f"'{func.__name__}' took {t * 1000:.2f} ms")
            return e.value

    return wrapper


async def api_token(token: str = Depends(APIKeyHeader(name="api-key"))):
    if token not in settings.API_KEY.get("api_key"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            result="fail",
        )


# @timed_execution_async
async def detect_objects(image_id, body) -> dict:
    connection = rabbitpy.Connection(settings.RABBITMQ_URL)
    channel = connection.channel()

    exchange = rabbitpy.DirectExchange(channel, "rpc-replies")
    exchange.declare()

    # queue_name = f"response-queue-{os.getpid()}"
    queue_name = f"response-queue-{uuid.uuid4()}"
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

    program_id = body["program_id"].split("_")[0]
    number = int(body["program_id"].split("_")[-1])
    image_url = body["image"]
    if not image_url[:8].startswith(("https://", "http://", "ftp://")):
        temp_file = utils.read_and_write_base64(image_url)
    elif image_url[:8].startswith("ftp://"):
        image_ftp_name = body["image"].split("/")[-1]
        image_ftp = f"{settings.FTP_URL}/{image_ftp_name}"
        temp_file = utils.read_and_write_url(image_ftp)
    else:
        temp_file = utils.read_and_write_url(image_url)

    if settings.DEBUG:
        print(f"Sending request for image: {image_url}")

    hash_value = hashlib.md5(image_url.encode())
    properties = {
        "app_id": "Publisher",
        "content_type": utils.mime_types(temp_file),
        "reply_to": queue_name,
        "headers": {"image-hash": str(hash_value.hexdigest())},
    }

    message = rabbitpy.Message(
        channel,
        utils.read_image(temp_file),
        properties,
        opinionated=True,
    )

    # Publish
    message.publish("rpc-requests")

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

    response_queue.delete()

    channel.close()
    connection.close()

    detection_dict, image_url = json.loads(message.body)

    # code new
    check = await Checks.get(id=program_id)
    check_dict = CheckPublic.from_orm(check).dict(
        exclude={"id", "name", "transform"}
    )

    matrix_check = check_dict["matrix"]
    image_result = "src/images/{}".format(image_url.split("/")[-1])

    result = State.PASS
    sum_check = 0
    sum_matrix = check_dict["count_face"] * number
    reason = ""

    for key, item in matrix_check.items():
        check_list = matrix_check[key].split("*")
        check_transform = int(check_list[0][1:])
        check_quant = int(check_list[1])
        if "&" in check_list:
            try:
                if check_quant * number > detection_dict[key]:
                    result = State.FAIL
                    reason += f"{key} thiếu {check_quant * number - detection_dict[key]}"
            except KeyError:
                result = State.FAIL
                reason += f"{key} thiếu {check_quant * number}"
        try:
            sum_check += detection_dict[key] * check_transform
        except KeyError:
            pass

    if result == State.PASS and sum_check < sum_matrix:
        result = State.FAIL
        reason = f"Bộ trưng bày {body['program_id']} thiếu {sum_matrix - sum_check} mặt"

    image_update = ImageUpdate(image_result=image_result, pass_fail=result)
    await Images.get(id=image_id).update(**image_update.dict())

    return {
        "result": result,
        "reason": reason,
        "program_id": body["program_id"],
        "image_url": image_url.split("/")[-1],
    }


# @timed_execution
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[
                {
                    "type": "string_type",
                    "loc": ["body", "image"],
                    "msg": f"Error reading image from URL: {e}",
                    "input": image_url,
                    "url": "https://errors.pydantic.dev/2.5/v/string_type",
                }
            ],
            result="fail",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[
                {
                    "type": "string_type",
                    "loc": ["body", "image"],
                    "msg": f"Error writing image to {filename}: {e}",
                    "input": image_url,
                    "url": "https://errors.pydantic.dev/2.5/v/string_type",
                }
            ],
            result="fail",
        )


# @timed_execution
def read_and_write_base64(image_b64):
    try:
        decoded = base64.b64decode(image_b64)
        h = hashlib.sha1()
        h.update(decoded)
        filename = f"{h.hexdigest()}.jpg"
        # Open the image using PIL
        image = Image.open(BytesIO(decoded))
        image = image.convert("RGB")

        # Save the image locally
        if not os.path.exists("src/tmp"):
            os.makedirs("src/tmp")
        filename = f"src/tmp/{filename}"
        image.save(filename)
        return filename
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[
                {
                    "type": "string_type",
                    "loc": ["body", "image"],
                    "msg": f"Error writing image to filename: {e}",
                    "input": image_b64,
                    "url": "https://errors.pydantic.dev/2.5/v/string_type",
                }
            ],
            result="fail",
        )
