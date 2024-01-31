from typing import Optional, Union

from pydantic import BaseModel, validator
from tortoise import fields, models

from src.settings import settings
from src.models.check import CheckPublic, Checks


class Images(models.Model):
    """
    The Image Display model
    """

    id = fields.IntField(pk=True)
    image = fields.CharField(max_length=128, unique=True)
    latitude = fields.FloatField()
    longitude = fields.FloatField()
    program: fields.ForeignKeyRelation[Checks] = fields.ForeignKeyField(
        "models.Checks", related_name="images", null=False
    )

    class Meta:
        table = "images"


from src.models.check import Checks


class Checks(Checks):
    images: fields.ReverseRelation["Images"]


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


class ImageBase(BaseModel):
    image: str
    location: Location
    program_id: int

    class Config:
        json_schema_extra = {
            "example": {
                "image": "http://10.20.1.90/image/002df0a7-25c2-47d0-b3e8-e513c3c0d9de.jpeg",
                "location": {"latitude": 16.0590299, "longitude": 108.2075305},
                "program_id": 2,
            }
        }


class ImageCreate(ImageBase):
    pass


class ImagePublic(ImageBase):
    id: int

    class Config:
        json_schema_extra = {
            "example": {
                "image": "src/tmp/5b77964d8e3024a252657ca4a75cb3ebbaeac074.jpg",
                "location": {"latitude": 16.0590299, "longitude": 108.2075305},
                "program_id": 2,
                "id": 10,
            }
        }


class ImageUpdate(BaseModel):
    program_id: int


class ImageDisplayPublic(BaseModel):
    result: str
    reason: str
    program_id: Optional[int]
    image_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "result": "Đạt",
                "reason": "",
                "program_id": 2,
                "image_url": "a82d779d5fe2565eb351bc1f828e779ff5637db3.jpg",
            }
        }
