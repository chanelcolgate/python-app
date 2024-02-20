import os
import json
import time
from typing import List, Any, Union, Dict, Optional

import cv2
import numpy
import requests
import rabbitpy
from fastapi import APIRouter, HTTPException, status, Query, Body, Depends
from tortoise.exceptions import DoesNotExist
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.query_utils import Prefetch
from tortoise.transactions import in_transaction

import utils
from src.models.image_display import (
    ImageDisplayPublic,
    ImageCreate,
    ImagePublic,
    ImageUpdate,
    Images,
    Checks,
    Location,
)
from src.models.check import CheckPublic
from src.settings import settings
from src.rabbitmq.connection import connection, channel, exchange
from src.utils import detect_objects, read_and_write_url, read_and_write_base64

image_display_router = APIRouter(tags=["Image Display"])


# Function to execute the raw SQL query
async def execute_query(latitude, longitude, program_id, limit):
    sql_query = f"""
        WITH distance AS (
            SELECT
                id,
                image,
                (((acos(sin(({latitude} * pi() / 180)) * sin(((latitude)::real * pi() / 180)) + cos(({latitude}* pi() / 180)) * cos(((latitude)::real * pi() / 180)) * cos((({longitude} - (longitude)::real) * pi() / 180)))) * 180 / pi()) * 60 * 1.1515 * 1.609344) * 1000 AS distance
            FROM
                images
            WHERE program_id = '{program_id}'
        )
        SELECT
            image
        FROM
            distance
        WHERE distance <= {limit} and distance > 0
        ORDER BY
            distance
        LIMIT 70;
    """

    async with in_transaction("default") as tconn:
        result = await tconn.execute_query_dict(sql_query)

    return result


# @image_display_router.post("/duplicate-image")
# async def create_duplicate_image(body: ImageCreate = Body(...)) -> dict:
#     body_json = body.dict(exclude_unset=True)
#     main_image_path = read_and_write_url(body_json["image"])
#     results = await execute_query(
#         latitude=body_json["location"]["latitude"],
#         longitude=body_json["location"]["longitude"],
#         limit=300,
#     )
#     for result in results:
#         main_image = cv2.imread(os.path.abspath(main_image_path))
#         gray_main_image = cv2.cvtColor(main_image, cv2.COLOR_BGR2GRAY)
#
#         template = cv2.imread(os.path.abspath(result["image"]), 0)
#         res = cv2.matchTemplate(gray_main_image, template, cv2.TM_CCOEFF_NORMED)
#         conf = round(res.max() * 100, 2)
#         if conf > 90:
#             return {
#                 "result": "Trùng",
#                 "image": body_json["image"],
#                 "program_id": body_json["program_id"],
#             }
#
#     try:
#         checks = await Checks.get(id=body_json["program_id"])
#     except DoesNotExist:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Checks {body_json['program_id']} does not exist",
#         )
#     await Images.create(
#         image=main_image_path,
#         latitude=body_json["location"]["latitude"],
#         longitude=body_json["location"]["longitude"],
#         program=checks,
#     )
#     return {
#         "result": "Không trùng",
#         "image": body_json["image"],
#         "program_id": body_json["program_id"],
#     }


# @image_display_router.post(
#     "/object-detection", response_model=ImageDisplayPublic
# )
# async def create_object_detection(
#     body: ImageCreate = Body(...),
# ) -> ImageDisplayPublic:
#     body_json = body.dict(exclude_unset=True)
#     filename = read_and_write_url(body_json["image"])
#     try:
#         checks = await Checks.get(id=body_json["program_id"])
#     except DoesNotExist:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Checks {body_json['program_id']} does not exist",
#         )
#
#     await Images.create(
#         image=filename,
#         latitude=body_json["location"]["latitude"],
#         longitude=body_json["location"]["longitude"],
#         program=checks,
#     )
#     result = await detect_objects(body_json)
#     return result


@image_display_router.post("/showroom-grading")
async def showroom_grading(body: ImageCreate = Body(...)) -> dict:
    body_json = body.dict(exclude_unset=True)
    if body_json["image"].startswith(("https://", "http://")):
        main_image_path = read_and_write_url(body_json["image"])
    else:
        main_image_path = read_and_write_base64(body_json["image"])

    results = await execute_query(
        latitude=body_json["location"]["latitude"],
        longitude=body_json["location"]["longitude"],
        program_id=body_json["program_id"].split("_")[0],
        limit=settings.LIMIT,
    )
    for result in results:
        main_image = cv2.imread(os.path.abspath(main_image_path))
        gray_main_image = cv2.cvtColor(main_image, cv2.COLOR_BGR2GRAY)

        template = cv2.imread(os.path.abspath(result["image"]), 0)
        res = cv2.matchTemplate(gray_main_image, template, cv2.TM_CCOEFF_NORMED)
        conf = round(res.max() * 100, 2)
        if conf > 90:
            return {
                "result": "Duplicated",
                "image": body_json["image"],
                "program_id": body_json["program_id"],
            }

    try:
        checks = await Checks.get(id=body_json["program_id"].split("_")[0])
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Checks {body_json['program_id']} does not exist",
        )
    image_obj = await Images.create(
        image=main_image_path,
        latitude=body_json["location"]["latitude"],
        longitude=body_json["location"]["longitude"],
        program=checks,
    )
    result = await detect_objects(image_obj.id, body_json)
    return result


@image_display_router.get("/", response_model=List[ImagePublic])
async def retrieve_all_checks() -> List[ImagePublic]:
    images = await Images.all().values(
        "id", "image", "latitude", "longitude", program_id="program__id"
    )
    return [
        ImagePublic(
            id=image["id"],
            image=image["image"],
            location=Location(
                latitude=image["latitude"], longitude=image["longitude"]
            ),
            program_id=image["program_id"],
        )
        for image in images
    ]


@image_display_router.get("/{id}", response_model=ImagePublic)
async def retrieve_image(id: int) -> ImagePublic:
    try:
        image = await Images.get(id=id).values(
            "id", "image", "latitude", "longitude", program_id="program__id"
        )
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return ImagePublic(
        id=image["id"],
        image=image["image"],
        location=Location(
            latitude=image["latitude"], longitude=image["longitude"]
        ),
        program_id=image["program_id"],
    )


@image_display_router.post("/new-image")
async def create_image(body: ImageCreate = Body(...)) -> dict:
    body_json = body.dict(exclude_unset=True)
    filename = read_and_write_url(body_json["image"])
    try:
        checks = await Checks.get(id=body_json["program_id"])
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Checks {body_json['program_id']} does not exist",
        )
    await Images.create(
        image=filename,
        latitude=body_json["location"]["latitude"],
        longitude=body_json["location"]["longitude"],
        program=checks,
    )
    return {"message": "Check created successfully"}


@image_display_router.put("/edit/{id}")
async def update_image(image_update: ImageUpdate, id: int) -> dict:
    try:
        check = await Checks.get(id=image_update.dict()["program_id"])
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Checks {image_update.dict()['program_id']} does not exist",
        )
    try:
        await Images.get(id=id).update(program=check)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {"message": "Image updated successuflly"}


@image_display_router.delete("/{program_id}")
async def delete_images(program_id: str) -> dict:
    try:
        images = await Images.filter(program__id=program_id)
        for image in images:
            os.unlink(os.path.abspath(image.image))
            await image.delete()
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Checks {program_id} does not exist",
        )
    return {"message": f"Deleted images filtered with {program_id}"}
