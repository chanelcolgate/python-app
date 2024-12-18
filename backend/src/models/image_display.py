from typing import Optional, Union
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, validator
from tortoise import fields, models

from src.settings import settings
from src.models.check import CheckPublic, Checks


class State(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class Images(models.Model):
    """
    The Image Display model
    """

    id = fields.IntField(pk=True)
    request_id = fields.CharField(max_length=128, null=False)
    # image = fields.CharField(max_length=128, unique=True)
    image = fields.CharField(max_length=128)
    latitude = fields.FloatField()
    longitude = fields.FloatField()
    program: fields.ForeignKeyRelation[Checks] = fields.ForeignKeyField(
        "models.Checks", related_name="images", null=False
    )
    image_result = fields.CharField(max_length=128, null=True)
    pass_fail = fields.CharEnumField(enum_type=State, default="fail")

    created_time = fields.DatetimeField(
        auto_now=False, auto_no_add=False, null=True
    )
    number = fields.IntField(null=True)
    ai_result = fields.JSONField(null=True)

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
    program_id: str
    request_id: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "image": "http://103.28.32.80:15433/image/3d48c4ea74ddec5c3804c64874df268c2a2a575e.jpg",
                "location": {"latitude": 16.0590299, "longitude": 108.2075305},
                "program_id": "LOCG_01",
                "request_id": "akdfhaldhfladfj",
            }
        }


class ImageCreate(ImageBase):
    pass


class ImagePublic(ImageBase):
    id: int
    request_id: str
    image_result: str
    pass_fail: State

    created_time: datetime
    number: int
    ai_result: dict

    class Config:
        json_schema_extra = {
            "example": {
                "image_result": "src/images/5aa181e6ca8f607be9b240904f9f245f0ed37e7b.jpg",
                "pass_fail": "pass",
                "image": "src/tmp/5b77964d8e3024a252657ca4a75cb3ebbaeac074.jpg",
                "location": {"latitude": 16.0590299, "longitude": 108.2075305},
                "program_id": "LOCG_01",
                "created_time": "2024-04-15 10:22:04.93517+00",
                "number": 1,
                "ai_result": '{"HOP_YTV": 3, "LOC_JUN": 2, "LOC_YTV": 1, "LOO_KID": 19, "LOO_YTV": 39}',
                "id": 10,
                "request_id": "aldfjladjf",
            }
        }


class ImageUpdate(BaseModel):
    image_result: Optional[str] = None
    pass_fail: Optional[State] = None
    number: Optional[int] = None
    ai_result: Optional[dict] = None


class ImageDisplayPublic(BaseModel):
    result: str
    reason: str
    program_id: Optional[str]
    image_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "result": "pass",
                "reason": "",
                "program_id": "HPLO_01",
                "image_url": "a82d779d5fe2565eb351bc1f828e779ff5637db3.jpg",
            }
        }
