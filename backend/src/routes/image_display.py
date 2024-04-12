import os
import json
import time
from typing import List, Any, Union, Dict, Optional

import cv2
import numpy
import requests
import rabbitpy
import imagehash
from PIL import Image
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
from src.utils import api_token, timed_execution, timed_execution_async, images_to_compare
from src.rabbitmq.connection import connection, channel, exchange
from src.utils import detect_objects, read_and_write_url, read_and_write_base64

image_display_router = APIRouter(tags=["Image Display"])


# Function to execute the raw SQL query
# @timed_execution_async
async def execute_query(latitude, longitude, program_id, limit):
    sql_query = f"""
        WITH distance AS (
            SELECT
                id,
                image,
                (((acos(sin(({latitude} * pi() / 180)) * sin(((latitude)::real * pi() / 180)) + cos(({latitude}* pi() / 180)) * cos(((latitude)::real * pi() / 180)) * cos((({longitude} - (longitude)::real) * pi() / 180)))) * 180 / pi()) * 60 * 1.1515 * 1.609344) * 1000 AS distance
            FROM
                images
            WHERE program_id = '{program_id}' and pass_fail = 'pass'
        )
        SELECT
            image
        FROM
            distance
        WHERE distance <= {limit} and distance >= 0
        ORDER BY
            distance
        LIMIT 70;
    """

    async with in_transaction("default") as tconn:
        result = await tconn.execute_query_dict(sql_query)

    return result

# def images_to_compare(img1, img2, func):
#     if func == imagehash.phash:
#         img1 = Image.fromarray(img1)
#         img2 = Image.fromarray(img2)
#         hash1 = func(img1)
#         hash2 = func(img2)
#         return hash1 - hash2
#     else:
#         try:
#             res = func(img1, img2, cv2.TM_CCOEFF_NORMED)
#         except Exception:
#             res = numpy.array([[0]])
#         return round(res.max() * 100, 2)


def images_to_compare_2(imfile1, imfile2, func):
    img1, img2 = Image.open(imfile1), Image.open(imfile2)
    hash1 = func(img1)
    hash2 = func(img2)
    return hash1 - hash2


@image_display_router.post("/duplicate-image")
async def create_duplicate_image(body: ImageCreate = Body(...)) -> dict:
    body_json = body.dict(exclude_unset=True)
    if body_json["image"].startswith(("https://", "http://")):
        main_image_path = read_and_write_url(body_json["image"])
    # ftp://mind@10.17.4.14/_G0600060_1705549132152.jpg
    elif body_json["image"].startswith("ftp://"):
        image_ftp_name = body_json["image"].split("/")[-1]
        image_ftp = f"{settings.FTP_URL}/{image_ftp_name}"
        main_image_path = read_and_write_url(image_ftp)
    else:
        main_image_path = read_and_write_base64(body_json["image"])

    results = await execute_query(
        latitude=body_json["location"]["latitude"],
        longitude=body_json["location"]["longitude"],
        program_id=body_json["program_id"].split("_")[0],
        limit=settings.LIMIT,
    )
    for result in results:
        conf_a = images_to_compare_2(
            os.path.abspath(main_image_path),
            os.path.abspath(result["image"]),
            imagehash.average_hash
        )
        # conf_p = images_to_compare_2(
        #     os.path.abspath(main_image_path),
        #     os.path.abspath(result["image"]),
        #     imagehash.phash
        # )
        # conf_d = images_to_compare_2(
        #     os.path.abspath(main_image_path),
        #     os.path.abspath(result["image"]),
        #     imagehash.dhash
        # )
        # conf_wh = images_to_compare_2(
        #     os.path.abspath(main_image_path),
        #     os.path.abspath(result["image"]),
        #     imagehash.whash
        # )
        # conf_wd = images_to_compare_2(
        #     os.path.abspath(main_image_path),
        #     os.path.abspath(result["image"]),
        #     lambda image: imagehash.whash(image, mode='db4')
        # )
        # conf_co = images_to_compare_2(
        #     os.path.abspath(main_image_path),
        #     os.path.abspath(result["image"]),
        #     imagehash.colorhash
        # )
        # conf_cr = images_to_compare_2(
        #     os.path.abspath(main_image_path),
        #     os.path.abspath(result["image"]),
        #     imagehash.crop_resistant_hash
        # )
        print("conf_a", conf_a)
        # print("conf_p", conf_p)
        # print("conf_d", conf_d)
        # print("conf_wh", conf_wh)
        # print("conf_wd", conf_wd)
        # print("conf_co", conf_co)
        # print("conf_cr", conf_cr)
        if conf_a < 15:
            return {
                "result": "duplicated",
                "image": body_json["image"],
                "program_id": body_json["program_id"],
            }
    return {
        "result": "no duplicated",
        "image": body_json["image"],
        "program_id": body_json["program_id"],
    }


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

from starlette.responses import JSONResponse, Response


@image_display_router.post(
    "/showroom-grading", dependencies=[Depends(api_token)]
)
async def showroom_grading(body: ImageCreate = Body(...)) -> dict:
    body_json = body.dict(exclude_unset=True)
    if body_json["image"].startswith(("https://", "http://")):
        main_image_path = read_and_write_url(body_json["image"])
    # ftp://mind@10.17.4.14/_G0600060_1705549132152.jpg
    elif body_json["image"].startswith("ftp://"):
        image_ftp_name = body_json["image"].split("/")[-1]
        image_ftp = f"{settings.FTP_URL}/{image_ftp_name}"
        main_image_path = read_and_write_url(image_ftp)
    else:
        main_image_path = read_and_write_base64(body_json["image"])

    results = await execute_query(
        latitude=body_json["location"]["latitude"],
        longitude=body_json["location"]["longitude"],
        program_id=body_json["program_id"].split("_")[0],
        limit=settings.LIMIT,
    )
    for result in results:
        conf =  images_to_compare(
            os.path.abspath(main_image_path),
            os.path.abspath(result["image"]),
            imagehash.average_hash
        )

        if conf < 15:
            return {
                "result": "duplicated",
                "image": body_json["image"],
                "program_id": body_json["program_id"],
            }

    try:
        checks = await Checks.get(id=body_json["program_id"].split("_")[0])
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chương trình {body_json['program_id']} không tồn tại",
            result="fail",
        )
    image_obj = await Images.create(
        image=main_image_path,
        latitude=body_json["location"]["latitude"],
        longitude=body_json["location"]["longitude"],
        program=checks,
    )
    result = await detect_objects(image_obj.id, body_json)
    return result


# @image_display_router.get(
#     "", response_model=List[ImagePublic], dependencies=[Depends(api_token)]
# )
# async def retrieve_all_checks() -> List[ImagePublic]:
#     images = await Images.all().values(
#         "id",
#         "image",
#         "latitude",
#         "longitude",
#         "image_result",
#         "pass_fail",
#         program_id="program__id",
#     )
#     return [
#         ImagePublic(
#             id=image["id"],
#             image=image["image"],
#             location=Location(
#                 latitude=image["latitude"], longitude=image["longitude"]
#             ),
#             program_id=image["program_id"],
#             image_result=image["image_result"],
#             pass_fail=image["pass_fail"],
#         )
#         for image in images
#     ]


# @image_display_router.get(
#     "/{id}", response_model=ImagePublic, dependencies=[Depends(api_token)]
# )
# async def retrieve_image(id: int) -> ImagePublic:
#     try:
#         image = await Images.get(id=id).values(
#             "id",
#             "image",
#             "latitude",
#             "longitude",
#             "image_result",
#             "pass_fail",
#             program_id="program__id",
#         )
#     except DoesNotExist:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
#     return ImagePublic(
#         id=image["id"],
#         image=image["image"],
#         location=Location(
#             latitude=image["latitude"], longitude=image["longitude"]
#         ),
#         program_id=image["program_id"],
#         image_result=image["image_result"],
#         pass_fail=image["pass_fail"],
#     )


# @image_display_router.post("/new-image")
# async def create_image(body: ImageCreate = Body(...)) -> dict:
#     body_json = body.dict(exclude_unset=True)
#     filename = read_and_write_url(body_json["image"])
#     try:
#         checks = await Checks.get(id=body_json["program_id"])
#     except DoesNotExist:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Checks {body_json['program_id']} does not exist",
#         )
#     await Images.create(
#         image=filename,
#         latitude=body_json["location"]["latitude"],
#         longitude=body_json["location"]["longitude"],
#         program=checks,
#     )
#     return {"message": "Check created successfully"}


# @image_display_router.put("/edit/{id}", dependencies=[Depends(api_token)])
# async def update_image(image_update: ImageUpdate, id: int) -> dict:
#     try:
#         await Images.get(id=id).update(**image_update.dict())
#     except DoesNotExist:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
#     return {"message": "Image updated successuflly"}


@image_display_router.delete("/{program_id}", dependencies=[Depends(api_token)])
async def delete_images(program_id: str) -> dict:
    try:
        await Checks.get(id=program_id)
        images = await Images.filter(program__id=program_id)
        for image in images:
            try:
                os.unlink(os.path.abspath(image.image))
            except Exception:
                pass
            # os.unlink(os.path.abspath(image.image_result))
            await image.delete()
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chương trình {program_id} không tồn tại",
            result="fail",
        )
    return {"message": f"Các bức ảnh được chấm điểm với mã chương trình {program_id} đã bị xóa"}
