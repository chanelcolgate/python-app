import hashlib
import imghdr
import os
import platform
import base64
from io import BytesIO

import requests
from PIL import Image


def mime_types(filename):
    """Return the mime_type of the file

    :param str filename: The path to the image file
    :rtype: str

    """
    return f"image/{imghdr.what(filename)}"


def read_image(filename):
    """Read in the file from path and return the opaque binary data

    :rtype str
    """
    with open(filename, "rb") as handle:
        return handle.read()


def read_and_write_url(image_url):
    h = hashlib.sha1()
    h.update(image_url.encode("utf-8"))
    filename = f"{h.hexdigest()}.jpg"
    try:
        # Make a GET requests to the image URL
        response = requests.get(image_url)
        response.raise_for_status()  # Check if the request was successfully

        # Open the image using PIL
        image = Image.open(BytesIO(response.content))
        image = image.convert("RGB")

        # Save the image locally
        operating_system = platform.system()

        if operating_system == "Windows":
            filename = f"C:\\Users\\NGUYEN~1\\AppData\\Local\\Temp\{filename}"
        else:
            filename = f"/tmp/{filename}"

        # Save the image locally
        image.save(filename)
        return filename
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error reading image from URL: {e}")
    except Exception as e:
        raise ValueError(f"Error writing image to {filename}: {e}")


def read_and_write_base64(image_b64):
    decoded = base64.b64decode(image_b64)
    h = hashlib.sha1()
    h.update(decoded)
    filename = f"{h.hexdigest()}.jpg"
    try:
        # Open the image using PIL
        image = Image.open(BytesIO(decoded))
        image = image.convert("RGB")

        # Save the image locally
        operating_system = platform.system()

        if operating_system == "Windows":
            fielname = f"C:\\Users\\NGUYEN~1\\AppData\\Local\\Temp\{filename}"
        else:
            filename = f"/tmp/{filename}"

        image.save(filename)
        return filename
    except Exception as e:
        raise ValueError(f"Error writing image to {filename}: {e}")


def write_temp_file(obd, mime_type):
    """Write out the binary data passed in to a temporary file,
    using the mime type to determine the file extension.

    :param str obd: The opaque binary data
    :param str mime_type: The image mime_type
    :rtype: str

    """
    h = hashlib.sha1()
    h.update(obd)
    if mime_type in ["image/jpg", "image/jpeg"]:
        filename = f"{h.hexdigest()}.jpg"
    elif mime_type == "image/png":
        filename = f"{h.hexdigest()}.png"
    else:
        raise ValueError(f"Unsupported mime-type: {mime_type}")

    operating_system = platform.system()

    if operating_system == "Windows":
        filename = f"C:\\Users\\NGUYEN~1\\AppData\\Local\\Temp\{filename}"
    else:
        filename = f"/tmp/{filename}"
    with open(filename, "wb") as handle:
        handle.write(obd)
    return filename
