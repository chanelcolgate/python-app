from typing import Optional, Union

from pydantic import BaseModel, validator
from tortoise import fields, models

from src.settings import Settings
from src.models.check import CheckPublic

settings = Settings()


class Location(BaseModel):
    latitude: float
    longitude: float

    class Config:
        json_schema_extra = {
            "example": {"latitude": 16.0590299, "longitude": 108.2075305}
        }


# class ImageDuplicate(BaseModel):
#     confidence: float
#     image_src: str
#
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "confidence": 57.59,
#                 "image_src": "http://10.20.1.90/image/fee8c9b5-21ad-4854-b7c6-5632f42e97e4.jpeg",
#             }
#         }


class ImageObjectDetection(BaseModel):
    image_src: str

    class Config:
        json_schema_extra = {
            "example": {
                "image_src": "http://10.20.1.90/image/fee8c9b5-21ad-4854-b7c6-5632f42e97e4.jpeg",
            }
        }


class ImageDisplayBase(BaseModel):
    image: str
    limit: int
    location: Location
    check: CheckPublic

    class Config:
        json_schema_extra = {
            "example": {
                "image": "http://10.20.1.90/image/002df0a7-25c2-47d0-b3e8-e513c3c0d9de.jpeg",
                "limit": 300,
                "location": {"latitude": 16.0590299, "longitude": 108.2075305},
                "check": {
                    "name": "hộp",
                    "type_check": "trưng bày base",
                    "hop_ytv": 4,
                    "hop_vtg": 1,
                    "hop_jn": 1,
                },
            }
        }


class ImageDisplayCreate(ImageDisplayBase):
    pass


class ImageDisplayPublic(ImageDisplayCreate):
    if settings.SHOW:
        id: int

    # duplicate: ImageDuplicate
    object_detection: ImageObjectDetection

    class Config:
        json_schema_extra = {
            "example": {
                "image": "http://10.20.1.90/image/002df0a7-25c2-47d0-b3e8-e513c3c0d9de.jpeg",
                "limit": 300,
                "location": {"latitude": 16.0590299, "longitude": 108.2075305},
                "check": {
                    "name": "hộp",
                    "type_check": "trưng bày base",
                    "hop_ytv": 4,
                    "hop_vtg": 1,
                    "hop_jn": 1,
                },
                "object_detection": {
                    "image_src": "https://jodies.de/ipcalc?host=172.25.0.0&mask1=20&mask2=29"
                },
            }
        }
